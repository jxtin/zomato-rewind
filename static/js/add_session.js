// ensure the value entered matches that of a phone number
function validatePhone(phone) {
    var re = /^\d{10}$/;
    return re.test(phone);
}
// generate a session id and store it with the client
function generateSessionId() {
    // generate a random number
    var sessionId = Math.floor(Math.random() * 1000000000);
    // store the session id in the client
    localStorage.setItem('sessionId', sessionId);
    // return the session id
    return sessionId;
}




function submitPhone() {
    // get the phone number entered
    var phone = document.getElementById('phone').value;
    // check if the phone number is valid
    if (validatePhone(phone)) {
        // disable the submit button
        document.getElementById('submit-phone').disabled = true;
        // if valid, send the phone number to the server
        fetch('/submit_phone', {
            method: 'POST',
            body: JSON.stringify({
                phone: phone,
                sessionId: sessionId
            })
        })
            .then(function (response) {
                // while the server is processing the request, show a loading gif
                document.getElementById('submit-phone').innerHTML = '<img src="https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif" width="30px" height="30px">';
                return response.json();
            }).then(function (data) {
                // remove the loading gif
                document.getElementById('submit-phone').innerHTML = 'Submit';
                // if the server returns a success message, update the form
                console.log(data);
                if (data.status == 200) {
                    // enable the submit button
                    document.getElementById('submit-phone').disabled = false;
                    updateForm();
                }
                else {
                    alert(data.message);
                    // enable the submit button
                    document.getElementById('submit-phone').disabled = false;
                }
            });

        // enable the submit button
    }
    else {
        // if the phone number is invalid, alert the user
        alert('Please enter a valid phone number');
    }
}

// when the submit button is clicked, call the submitButton function

function updateForm() {
    // add otp input field
    var otpInput = document.createElement('input');
    otpInput.setAttribute('type', 'text');
    otpInput.setAttribute('class', 'form-control');
    otpInput.setAttribute('id', 'otp');
    otpInput.setAttribute('placeholder', 'OTP');
    // update submit button
    document.getElementById('submit-phone').removeEventListener('click', submitPhone);

    var submitButton = document.getElementById('submit-phone');
    submitButton.innerHTML = 'Verify';
    submitButton.setAttribute('id', 'submit-otp');
    // add the otp input field to the form
    document.getElementById('inputs').appendChild(otpInput);
    // when the submit button is clicked, call the verifyOtp function
    document.getElementById('submit-otp').addEventListener('click', verifyOtp);
    // remove the previous listener
}

function verifyOtp() {
    // get the otp entered
    var otp = document.getElementById('otp').value;
    var phone = document.getElementById('phone').value;
    // otp should be 6 digits, only numbers
    if (otp.length != 6 || isNaN(otp)) {
        alert('Please enter a valid OTP');
        return;
    }

    // disable the submit button
    document.getElementById('submit-otp').disabled = true;

    // send the otp to the server
    fetch('/verify_otp', {
        method: 'POST',
        body: JSON.stringify({
            otp: otp,
            phone: phone,
            sessionId: sessionId
        })
    })
        .then(function (response) {
            // while the server is loading show a loading gif
            return response.json();
        }).then(function (data) {
            // remove the loading gif
            document.getElementById('submit-otp').innerHTML = 'Verify';
            // if the server returns a success message, update the form
            console.log(data);
            if (data.status == 200) {
                alert('Login successful');
                // redirect to visualisation page
                window.location.href = '/visualisations';
            }
            else {
                alert(data.message);
            }
        });
}
