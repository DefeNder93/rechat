/**
 * A controller to manage news feed
 * @class
 */
angular.module('reChat.feedCtrl', [])
    .controller('FeedCtrl', ['$scope',
        function($scope) {

            console.log("init feed ctrl");

            $scope.message = "Write letter";

            $scope.sendMessage = function() {
                i++;
                $scope.comments.unshift({
                    author: "Петр" + i,
                    text: $scope.message
                });
                $scope.message = "";
            };

            $scope.comments = [  // TODO get from server
                {
                    author: "Иван1",
                    text: "Текст письма1"
                },
                {
                    author: "Иван2",
                    text: "Текст письма2"
                },
                {
                    author: "Иван3",
                    text: "Текст письма3"
                },
                {
                    author: "Иван4",
                    text: "Текст письма4"
                },
                {
                    author: "Иван5",
                    text: "Текст письма5"
                },
                {
                    author: "Иван6",
                    text: "Текст письма6"
                },
                {
                    author: "Иван7",
                    text: "Текст письма7"
                },
                {
                    author: "Иван8",
                    text: "Текст письма8"
                },
                {
                    author: "Иван9",
                    text: "Текст письма9"
                },
                {
                    author: "Иван10",
                    text: "Текст письма10"
                },
                {
                    author: "Иван11",
                    text: "Текст письма11"
                },
                {
                    author: "Иван12",
                    text: "Текст письма12"
                },
                {
                    author: "Иван13",
                    text: "Текст письма13"
                },
                {
                    author: "Иван14",
                    text: "Текст письма14"
                },
                {
                    author: "Иван15",
                    text: "Текст письма15"
                },
                {
                    author: "Иван16",
                    text: "Текст письма16"
                },
                {
                    author: "Иван17",
                    text: "Текст письма17"
                },
                {
                    author: "Иван18",
                    text: "Текст письма18"
                },
                {
                    author: "Иван19",
                    text: "Текст письма19"
                },
                {
                    author: "Иван20",
                    text: "Текст письма20"
                }
            ];

            var i = 21;
            $scope.myPagingFunction = function() {
                console.log("myPagingFunction");
                for (j=0;j<=30;j++) {
                    $scope.comments.push({
                        author: "Иван" + i,
                        text: "Текст письма" + i
                    });
                    i++;
                }
            };

        }]);