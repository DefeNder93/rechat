function crossDomainAjax(url, postdata, successCallback) {
    // IE8 & 9 only Cross domain JSON GET request
    if ('XDomainRequest' in window && window.XDomainRequest !== null) {

        var xdr = new XDomainRequest(); // Use Microsoft XDR
        xdr.open('post', url);
        xdr.onload = function () {
            successCallback(xdr.responseText);
        };

        xdr.onerror = function () {
            console.log("XDomainRequest failure, url: ", url);
        };

        xdr.send(postdata);
    } // IE7 and lower can't do cross domain XXX browser detection
    else if (oprobject.browser_info.browser.name === 'ie'
        && oprobject.browser_info.browser.version !== null
        && oprobject.browser_info.browser.version[0] < 8) {
        return false;
    } // Do normal jQuery AJAX for everything else
    else {
        $.post(url, postdata, successCallback);
    }
}


var jsonrpc_req_id = 0;
var JSONRPC_TIMEOUT = 10000; //10 seconds
var JSONRPC_URL = '/ajax';

function sendJSONRPC(url, method, params, onResponse, onError) {
    var request = {};
    jsonrpc_req_id = jsonrpc_req_id + 1;
    request.id = jsonrpc_req_id;
    request.jsonrpc = "2.0";
    request.method = method;
    if (params)
        request.params = params;

    var jqxhr = $.ajax({
        type: "POST",
        url: url,
        data: JSON.stringify(request),
        dataType: "json",
        contentType: "application/json; charset=utf-8",
        timeout: JSONRPC_TIMEOUT,
    })
        .done(function (response, textStatus) {
            //console.log("AJAX response ", response, "textStatus: ', textStatus);

            /* server returns with Content-Type: application/json but not all browsers parse JSON string (seems in case of CORS) */
            if (typeof response === "string")
                response = JSON.parse(response);

            onResponse(response);
        })
        .fail(function (jqXHR, textStatus) {
            //console.log("AJAX error, textStatus: ",textStatus );
            if (onError)
                onError(textStatus);
        });
}
