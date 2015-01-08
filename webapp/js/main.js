// 'use strict';
$(function() {
    function update_user_info(set_timeout) {
        sendJSONRPC(JSONRPC_URL, "user_sessions", null, function (response) {
            if (response.status == "error")
                alert(response.message);
            else {
                var i = "i am here";
                console.log(i)
            }
        });

        if (set_timeout == undefined || set_timeout)
            setTimeout(update_user_info, 10000);
    }

    function logout() {
        sendJSONRPC(JSONRPC_URL, "logout", null, function (response) {
            if (response.status == "error")
                alert("Logging out failed: " + response.message)
            window.location = "/"
        });
    }

    function unregister() {
        sendJSONRPC(JSONRPC_URL, "unregister", null, function (response) {
            if (response.status == "error")
                alert("Unregistering failed: " + response.message)
            window.location = "/"
        });
    }
});