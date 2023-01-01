
function fetchData() {
    document.querySelector("#download-button").disabled = true;
    phone_number = document.querySelector(".dropdown-toggle").innerHTML.slice(0, 10);
    fetch('/fetch_data', {
        method: 'POST',
        body: JSON.stringify({
            phone_number: phone_number
        })
    })
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            if (data["status"] == 200) {
                session_select_buttons.forEach(function (button) {
                    if (button.innerHTML == phone_number) {
                        // change the class of the button to btn btn-success
                        button.classList.remove("btn-info");
                        button.classList.add("btn-success");
                    }
                })
                alert("Data fetched successfully");
                // set the class="dropdown-toggle btn btn-primary" button innerHTML to phone_number
                document.querySelector(".dropdown-toggle").innerHTML = phone_number;

                document.querySelector("#download-button").disabled = false;
                // enable the button with id les-go
                document.querySelector("#les-go").disabled = false;


            }
        })


}



function getStats() {
    // get the phone number of the session
    var phone_number = document.querySelector(".dropdown-toggle").innerHTML;
    // disable the button with id les-go
    document.querySelector("#les-go").disabled = true;
    // make a post request to /get_stats with phone_number as the data
    fetch('/get_stats', {
        method: 'POST',
        body: JSON.stringify({
            phone_number: phone_number
        })
    })
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            // set the innerHTML of the stats to the data
            stats = data["stats"];
            // <ul class="stats">
            //     <li class="stat"></li>
            // </ul>

            // get the ul element with class stats
            var ul = document.querySelector(".stats");
            // remove all children of the ul element
            ul.innerHTML = "";
            // for each stat in stats
            stats.forEach(function (stat) {
                // create a li element
                var li = document.createElement("li");
                // set the class of the li element to stat
                li.classList.add("stat");
                // set the innerHTML of the li element to stat
                li.innerHTML = stat;
                // append the li element to the ul element
                ul.appendChild(li);
            });
            // enable the button with id les-go
            document.querySelector("#les-go").disabled = false;

        })
}


function displayGraphs() {
    phone_number = document.querySelector(".dropdown-toggle").innerHTML;
    var modal = document.getElementById("visualisationModal");
    var span = document.getElementsByClassName("close")[0];

    modal.style.display = "block";
    // get image from server
    // /visualisations/<phone_num>
    fetch('/visualisations/' + phone_number)
        .then(function (response) {
            // convert blob to base64
            return response.blob();
        }
        )
        .then(function (data) {
            // convert blob to base64
            var reader = new FileReader();
            reader.readAsDataURL(data);
            reader.onloadend = function () {
                base64data = reader.result;
                // set the src of the image to the base64 data
                document.getElementsByClassName("visualisation_img")[0].src = base64data;
            }
        });
}
