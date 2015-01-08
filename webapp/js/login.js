// 'use strict';
$(function() {
    function getURLParameter(name) {
        return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search) || [, ""])[1].replace(/\+/g, '%20')) || null;
    }

    $('#login-form').submit(function (event) {
        sendJSONRPC(JSONRPC_URL, "login", {username: $('#login-login').val(), password: $('#login-password').val() }, function (response) {
            if (response.status == "error") {
                $("#login-error").text(response.message);
            }
            else {
                next = getURLParameter('next');
                if (!next) {
                    next = "/"
                }
                window.location = next
            }
        });
        return false
    })

    $('#login-register').click(function (event) {
        window.location = "/register" //TODO rewrite human way
        return false
    })
});