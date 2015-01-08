/**
 * A controller to manage header
 * @class
 */
angular.module('reChat.headerCtrl', [])
    .controller('HeaderCtrl', ['$scope','$location',
        function($scope, $location) {

            $scope.radioModel = 'Feed';

            $scope.changeRoute = function(type) {
                switch (type) {
                    case "feed":
                        $location.path("/feed");
                        break;
                    case "chat":
                        $location.path("/chat");
                        break;
                }
            };

    }]);
