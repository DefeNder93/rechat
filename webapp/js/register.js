$(function() {
    // 'use strict';
    function getURLParameter(name) {
        return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search) || [, ""])[1].replace(/\+/g, '%20')) || null;
    }

    $('#register-form').submit(function (event) {
        var isRegistered = 0;
        console.log("sdfa");
        sendJSONRPC(JSONRPC_URL, "register", {username: $('#register-login').val(), password: $('#register-password').val() }, function (response) { //$('#register-secret').val()
            if (response.status == "error") {
                $("#register-error").text(response.message);
            }
            else {
                $("#register-error").text("successfully registered")
                var isRegistered = 1;
                sendJSONRPC(JSONRPC_URL, "login", {username: $('#register-login').val(), password: $('#register-password').val() }, function (response) {
                    if (response.status == "error") {
                        $("#register-error").text(response.message);
                    }
                    else {
                        var next = getURLParameter('next');
                        if (!next) {
                            next = "/"
                        }
                        window.location = next
                    }
                });
                return false
            }
        });
        console.log(isRegistered);
        return false
    })
});