import json
import pandas
import datetime


def clean_order_amt(order_amt):
    order_amt = float("".join(c for c in order_amt if c.isdigit() or c == "."))
    return round(order_amt, 2)


class User_data:
    def __init__(self, phone_number):
        with open(f"order_data/{phone_number}_orders.json", "r") as f:
            all_orders = json.load(f)

        self.orders = []
        for currpage in all_orders:
            for _, v in currpage["entities"]["ORDER"].items():
                if v["deliveryDetails"]["deliveryLabel"] == "Delivered":
                    self.orders.append(v)

        self.minimal_orders = self.minimise_orders()
        if len(self.minimal_orders) > 0:
            self.pd_df = pandas.DataFrame(self.minimal_orders)

            # city stats need to be calculated separately because they are not stored in the json file
            self.city_stats = self.get_city_stats()
            self.most_common = {}
            self.most_common["address"] = self.get_most_common("address")
            self.most_common["restaurant"] = self.get_most_common("restaurant")

    def get_city_stats(self):
        city_total = {}

        for order in self.orders:
            # '/city/resname'
            city = order["resInfo"]["resPath"].split("/")[1]
            cost = clean_order_amt(order["totalCost"])
            if city in city_total:
                city_total[city] += cost
            else:
                city_total[city] = cost
        # sort by value
        city_total = dict(
            sorted(city_total.items(), key=lambda item: item[1], reverse=True)
        )

        # generate a string for each city
        city_stats = []
        # if there are more than 5 cities, only show the top 5
        for city, total in city_total.items():
            city_stats.append((city, int(total)))
            if len(city_stats) == 5:
                break

        return city_stats

    def minimise_orders(self):
        minimal_orders = []
        for order in self.orders:
            minimal_orders.append(
                {
                    "restaurant": order["resInfo"]["name"],
                    "amount": clean_order_amt(order["totalCost"]),
                    "address": order["deliveryDetails"]["deliveryAddress"],
                    "datetime": datetime.datetime.strptime(
                        order["orderDate"], "%B %d, %Y at %I:%M %p"
                    ),
                }
            )
        return minimal_orders

    def get_most_common(self, column):
        if column == "restaurant":
            restaurants = [order["restaurant"] for order in self.minimal_orders]
            # return restaurant, count, and money spent
            # return (restaurant, count, money_spent)
            response = {
                "restaurant": max(set(restaurants), key=restaurants.count),
                "count": restaurants.count(
                    max(set(restaurants), key=restaurants.count)
                ),
                "money_spent": int(
                    sum(
                        [
                            order["amount"]
                            for order in self.minimal_orders
                            if order["restaurant"]
                            == max(set(restaurants), key=restaurants.count)
                        ]
                    )
                ),
            }
            return response

        elif column == "address":
            addresses = [order["address"] for order in self.minimal_orders]
            # return address, count, and money spent
            # return (address, count, money_spent)
            response = {
                "address": max(set(addresses), key=addresses.count),
                "count": addresses.count(max(set(addresses), key=addresses.count)),
                "money_spent": sum(
                    [
                        order["amount"]
                        for order in self.minimal_orders
                        if order["address"] == max(set(addresses), key=addresses.count)
                    ]
                ),
            }
            return response

        elif column == "date":
            # list of dates
            dates = [order["datetime"].date() for order in self.minimal_orders]
            return max(set(dates), key=dates.count)

    def get_total_spent(self):
        spent = 0
        for order in self.minimal_orders:
            spent += order["amount"]
        return int(spent)

    def get_total_orders(self):
        return len(self.minimal_orders)

    def get_total_restaurants(self):
        restaurants = set()
        for order in self.minimal_orders:
            restaurants.add(order["restaurant"])
        return len(restaurants)

    def money_spent_per_restaurant(self):
        money_spent_per_restaurant = {}
        for order in self.minimal_orders:
            if order["restaurant"] in money_spent_per_restaurant:
                money_spent_per_restaurant[order["restaurant"]] += order["amount"]
            else:
                money_spent_per_restaurant[order["restaurant"]] = order["amount"]

        # sort by value
        money_spent_per_restaurant = dict(
            sorted(
                money_spent_per_restaurant.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

        if len(money_spent_per_restaurant) > 5:
            money_spent_per_restaurant = list(money_spent_per_restaurant.items())[:5]
        else:
            money_spent_per_restaurant = list(money_spent_per_restaurant.items())

        return money_spent_per_restaurant

    def money_spent_per_address(self):
        # return desc sorted, top 10 if there are more than 10
        money_spent_per_address = {}
        for order in self.minimal_orders:
            if order["address"] in money_spent_per_address:
                money_spent_per_address[order["address"]] += order["amount"]
            else:
                money_spent_per_address[order["address"]] = order["amount"]

        # sort by value
        money_spent_per_address = dict(
            sorted(
                money_spent_per_address.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

        if len(money_spent_per_address) > 5:
            money_spent_per_address = list(money_spent_per_address.items())[:5]
        else:
            money_spent_per_address = list(money_spent_per_address.items())

        return money_spent_per_address

    def display_stats(self):
        # generate interesting strings from the data
        print(f"Total orders: {self.get_total_orders()}")
        print(f"Total restaurants: {self.get_total_restaurants()}")
        print(f"Total spent: {self.get_total_spent()}")

    def generate_stat_str(self):
        stats = []
        # if there are no orders then return a string saying so
        if self.get_total_orders() == 0:
            stats.append("You have no orders yet.")
            return stats
        else:
            stats.append(f"You placed <b>{self.get_total_orders()}</b> orders.")
            stats.append(
                f"Total restaurants explored <b>{self.get_total_restaurants()}</b>."
            )
            stats.append(f"And spent inr. <b>{self.get_total_spent()}</b>.")
            stats.append(
                f"Most common restaurant: <b>{self.most_common['restaurant']['restaurant']}</b> with <b>{self.most_common['restaurant']['count']}</b> orders and inr. <b>{self.most_common['restaurant']['money_spent']}</b> spent."
            )
            stats.append(
                f"Most common address: {self.most_common['address']['address']} with <b>{self.most_common['address']['count']}</b> orders and inr. <b>{self.most_common['address']['money_spent']}</b> spent."
            )
            money_spent_per_restaurant = "Money spent per restaurant: <br>"
            for restaurant in self.money_spent_per_restaurant():
                money_spent_per_restaurant += f"{restaurant[0].capitalize()}: inr. <b>{int(restaurant[1])}</b><br>"
            stats.append(money_spent_per_restaurant)
            money_spent_per_address = "Money spent per address: <br>"
            for address in self.money_spent_per_address():
                money_spent_per_address += (
                    f"{address[0].capitalize()}: inr. <b>{int(address[1])}</b><br>"
                )
            stats.append(money_spent_per_address)

            city_stats = "Money spent per city: \n<br>"
            for city in self.city_stats:
                city_stats += f"{city[0]}: inr. <b>{city[1]}</b>\n<br>"
            stats.append(city_stats)
            return stats


if __name__ == "__main__":
    user = User_data("7999580495")
    # user.display_stats()
    print(user.generate_stat_str())
