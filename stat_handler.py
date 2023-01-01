import json
import pandas
import os
import datetime
import july
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image


def clean_order_amt(order_amt):
    order_amt = float("".join(c for c in order_amt if c.isdigit() or c == "."))
    return round(order_amt, 2)


def get_dishlist(dish_string_string):
    dish_list = dish_string_string.split(", ")
    dish_with_count = {}
    for dish in dish_list:
        dish = dish.strip()
        if " x " in dish:
            dish_count, dish_name = dish.split(" x ")
            dish_with_count[dish_name] = int(dish_count)
        else:
            dish_with_count[dish] = 1
    return dish_with_count


class User_data:
    def __init__(self, phone_number):
        self.phone_number = phone_number
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

        self.date2ordercount = self.get_date2ordercount()

    def get_date2ordercount(self):
        date2ordercount = {}
        for order in self.minimal_orders:
            date = order["datetime"].date()
            if date in date2ordercount:
                date2ordercount[date] += 1
            else:
                date2ordercount[date] = 1
        # make it a dataframe
        date2ordercount = pandas.DataFrame(
            list(date2ordercount.items()), columns=["date", "order_count"]
        )
        date2ordercount["date"] = pandas.to_datetime(date2ordercount["date"])
        date2ordercount = date2ordercount.sort_values(by="date")
        return date2ordercount

    def get_city_stats(self):
        city_total = {}

        for order in self.minimal_orders:
            if order["city"] in city_total:
                city_total[order["city"]] += order["amount"]
            else:
                city_total[order["city"]] = order["amount"]

        # sort by value
        city_total = dict(
            sorted(city_total.items(), key=lambda item: item[1], reverse=True)
        )

        return city_total

    def minimise_orders(self):
        minimal_orders = []
        for order in self.orders:
            minimal_orders.append(
                {
                    "restaurant": order["resInfo"]["name"],
                    "city": order["resInfo"]["resPath"].split("/")[1],
                    "amount": clean_order_amt(order["totalCost"]),
                    "address": order["deliveryDetails"]["deliveryAddress"],
                    "datetime": datetime.datetime.strptime(
                        order["orderDate"], "%B %d, %Y at %I:%M %p"
                    ),
                    "dishes": get_dishlist(order["dishString"]),
                }
            )
        # print(minimal_orders[:10])
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
            stats.append(f"And spent ₹<b>{self.get_total_spent()}</b>.")
            stats.append(
                f"Most common restaurant: <b>{self.most_common['restaurant']['restaurant']}</b> with <b>{self.most_common['restaurant']['count']}</b> orders and ₹<b>{self.most_common['restaurant']['money_spent']}</b> spent."
            )
            # most common dish
            most_common_dish = "Most common dishes: <br>"
            # only top 7
            if len(self.get_common_dishes()) > 7:
                for dish in list(self.get_common_dishes().items())[:7]:
                    most_common_dish += (
                        f"{dish[0].capitalize()}: <b>{dish[1]}</b> times<br>"
                    )
                else:
                    most_common_dish += (
                        f"{dish[0].capitalize()}: <b>{dish[1]}</b> times<br>"
                    )
                stats.append(most_common_dish)

            # city_stats
            city_stats = "City stats: <br>"
            for city in self.city_stats:
                city_stats += f"{city.capitalize()}: <b>₹{int(self.city_stats[city])}</b> spent<br>"
            stats.append(city_stats)

            stats.append(
                f"Most common address: {self.most_common['address']['address']} with <b>{self.most_common['address']['count']}</b> orders and ₹<b>{self.most_common['address']['money_spent']}</b> spent."
            )
            money_spent_per_restaurant = "Money spent per restaurant: <br>"
            for restaurant in self.money_spent_per_restaurant():
                money_spent_per_restaurant += (
                    f"{restaurant[0].capitalize()}: ₹<b>{int(restaurant[1])}</b><br>"
                )
            stats.append(money_spent_per_restaurant)
            money_spent_per_address = "Money spent per address: <br>"
            for address in self.money_spent_per_address():
                money_spent_per_address += (
                    f"{address[0].capitalize()}: ₹<b>{int(address[1])}</b><br>"
                )
            stats.append(money_spent_per_address)

            return stats

    def get_common_dishes(self):
        # return a dict of the most common dishes
        most_common_dishes = {}
        for order in self.minimal_orders:
            for dish in order["dishes"]:
                if dish in most_common_dishes:
                    most_common_dishes[dish] += 1
                else:
                    most_common_dishes[dish] = 1

        # sort by value
        most_common_dishes = dict(
            sorted(
                most_common_dishes.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )

        return most_common_dishes

    def money_spent_per_month(self):
        money_spent_per_month = {}
        # consider only orders post 2021
        for order in self.minimal_orders:
            if order["datetime"].year > 2021:
                if order["datetime"].month in money_spent_per_month:
                    money_spent_per_month[order["datetime"].month] += order["amount"]
                else:
                    money_spent_per_month[order["datetime"].month] = order["amount"]

        # sort by date

        return money_spent_per_month

    def generate_line_chart(self):
        # generate a line chart of the money spent per month
        # line and text should be white
        # background should be transparent
        money_spent_per_month = self.money_spent_per_month()
        # print(money_spent_per_month)

        plt.clf()
        plt.figure(figsize=(10, 10), facecolor="#cb202d")
        plt.plot(
            list(money_spent_per_month.keys()),
            list(money_spent_per_month.values()),
            color="white",
        )
        # axes facecolor = #cb202d
        plt.gca().set_facecolor("#cb202d")
        # no border
        plt.gca().spines["top"].set_visible(False)
        plt.gca().spines["right"].set_visible(False)
        # for bottom and left set color to white
        plt.gca().spines["bottom"].set_color("white")
        plt.gca().spines["left"].set_color("white")

        # the values on the axes should be white
        plt.gca().tick_params(axis="x", colors="white")
        plt.gca().tick_params(axis="y", colors="white")

        plt.xlabel("Date", color="white")
        plt.ylabel("Money spent", color="white")
        plt.title("Money spent per month", color="white", fontsize=30)
        plt.savefig(
            f"visualisations/line_chart_{self.phone_number}.png", transparent=False
        )

    def generate_heatmap(self):
        # keep dates post 2020
        self.date2ordercount = self.date2ordercount[
            self.date2ordercount.date.dt.year > 2021
        ]
        # can the background be transparent?
        july.heatmap(
            self.date2ordercount.date,
            self.date2ordercount.order_count,
            cmap="Reds",
            colorbar=True,
            rc_params_dict={
                "figure.figsize": (5, 5),
            },
        ).figure.savefig(
            f"visualisations/heatmap_{self.phone_number}.png",
        )

    def generate_wordcloud(self):
        # generate a wordcloud of the most common words in the restaurant names
        # generate a string of all the food items ordered
        dishes_text_string = ""
        for order in self.minimal_orders:
            for item in order["dishes"].keys():
                dishes_text_string += (f"{item} ") * order["dishes"][item]
        # generate the wordcloud
        wordcloud = WordCloud(
            background_color="white",
            width=1000,
            height=500,
            max_words=200,
            max_font_size=300,
        ).generate(dishes_text_string)
        # save the wordcloud
        wordcloud.to_file(f"visualisations/wordcloud_{self.phone_number}.png")

    def generate_pie_chart(self):
        # reset plt
        plt.clf()
        # cities less than 1% of the total money spent will be grouped into "other"
        pie_chart_cities = self.city_stats.copy()
        pie_chart_cities["other"] = 0
        for city in self.city_stats:
            if self.city_stats[city] / self.get_total_spent() < 0.01:
                pie_chart_cities["other"] += self.city_stats[city]
                del pie_chart_cities[city]
        # generate the pie chart
        plt.pie(
            pie_chart_cities.values(),
            labels=pie_chart_cities.keys(),
            autopct="%1.1f%%",
            pctdistance=0.9,
            startangle=90,
        )
        # save the pie chart
        plt.savefig(f"visualisations/pie_chart_{self.phone_number}.png")

    def generate_visualisations(self):
        self.generate_heatmap()
        self.generate_wordcloud()
        self.generate_pie_chart()
        self.generate_line_chart()
        # stitch the images together into a single image
        # get the images
        heatmap = Image.open(f"visualisations/heatmap_{self.phone_number}.png")
        wordcloud = Image.open(f"visualisations/wordcloud_{self.phone_number}.png")
        pie_chart = Image.open(f"visualisations/pie_chart_{self.phone_number}.png")
        line_chart = Image.open(f"visualisations/line_chart_{self.phone_number}.png")
        heatmap = heatmap.crop((0, 0, heatmap.size[0], int(heatmap.size[1] * 0.7)))
        heatmap = heatmap.crop(
            (0, int(heatmap.size[1] * 0.45), heatmap.size[0], heatmap.size[1])
        )
        heatmap = heatmap.crop(
            (int(heatmap.size[0] * 0.1), 0, heatmap.size[0], heatmap.size[1])
        )
        heatmap = heatmap.crop((0, 0, int(heatmap.size[0] * 0.95), heatmap.size[1]))

        # heatmap should be on the top with its width being 1000 and height value to preserve aspect ratio
        heatmap = heatmap.resize((1000, int(heatmap.size[1] * 1000 / heatmap.size[0])))
        # below the heatmap should be the wordcloud
        wordcloud = wordcloud.resize(
            (1000, int(1000 * wordcloud.size[1] / wordcloud.size[0]))
        )
        pie_chart = pie_chart.crop(
            (int(pie_chart.size[0] * 0.33), 0, pie_chart.size[0], pie_chart.size[1])
        )
        pie_chart = pie_chart.crop(
            (0, 0, int(pie_chart.size[0] * 0.6), pie_chart.size[1])
        )
        pie_chart = pie_chart.crop(
            (0, int(pie_chart.size[1] * 0.1), pie_chart.size[0], pie_chart.size[1])
        )
        pie_chart = pie_chart.crop(
            (0, 0, pie_chart.size[0], int(pie_chart.size[1] * 0.85))
        )

        pie_chart = pie_chart.resize((500, 500))
        line_chart = line_chart.resize((500, 500))
        height = heatmap.size[1] + wordcloud.size[1] + pie_chart.size[1] + 10 * 2
        width = 1000
        new_image = Image.new("RGB", (width, height), (255, 255, 255))
        new_image.paste(heatmap, (0, 0))
        new_image.paste(wordcloud, (0, heatmap.size[1] + 10))
        new_image.paste(pie_chart, (0, heatmap.size[1] + wordcloud.size[1] + 20))
        new_image.paste(line_chart, (500, heatmap.size[1] + wordcloud.size[1] + 20))
        # save the image
        new_image.save(f"visualisations/{self.phone_number}.png")
        # delete the individual images
        os.remove(f"visualisations/heatmap_{self.phone_number}.png")
        os.remove(f"visualisations/wordcloud_{self.phone_number}.png")
        os.remove(f"visualisations/pie_chart_{self.phone_number}.png")
        os.remove(f"visualisations/line_chart_{self.phone_number}.png")


if __name__ == "__main__":
    user = User_data("7999580495")
    # user.display_stats()
    # print(user.generate_stat_str())
    user.generate_visualisation()
