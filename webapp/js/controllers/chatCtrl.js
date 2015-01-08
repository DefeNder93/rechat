/**
 * A controller to manage chat
 * @class
 */
angular.module('reChat.chatCtrl', [])
    .controller('ChatCtrl', ['$scope',
        function($scope) {

            $scope.isCreateRoomCollapsed = true;
            $scope.isInviteCollapsed = true;

            console.log("init chat ctrl");

            $scope.message = "Write message";

            $scope.sendMessage = function() {
                i++;
                $scope.comments.unshift({
                    author: "Петр" + i,
                    text: $scope.message
                });
                $scope.message = "";
            };

            $scope.toggleInviteCollapse = function() {
                $scope.isInviteCollapsed = !$scope.isInviteCollapsed;
                $scope.isCreateRoomCollapsed = true;
            };

            $scope.sendInvite = function() {
                if ($scope.invitedName.length > 0) {
                    $scope.isInviteCollapsed = true;
                }
                $scope.invitedName = "";
            };

            $scope.toggleRoomCollapse = function() {
                $scope.isCreateRoomCollapsed = !$scope.isCreateRoomCollapsed;
                $scope.isInviteCollapsed = true;
            };

            $scope.createRoom = function() {
                if ($scope.roomName.length > 0) {
                    $scope.rooms.push(
                        {name: $scope.roomName}
                    );
                    $scope.isCreateRoomCollapsed = true;
                }
                $scope.roomName = "";
            };

            $scope.isSettingsCollapsed = true;

            $scope.rooms = [
                { name: "room 10" },
                { name: "925" },
                { name: "a lot of fun here" },
                { name: "Комната отдыха" }
            ];

            $scope.comments = [ // TODO get from server
                {
                    author: "Иван1",
                    text: "Текст комментария1"
                },
                {
                    author: "Иван2",
                    text: "Текст комментария2"
                },
                {
                    author: "Иван3",
                    text: "Текст комментария3"
                },
                {
                    author: "Иван4",
                    text: "Текст комментария4"
                },
                {
                    author: "Иван5",
                    text: "Текст комментария5"
                },
                {
                    author: "Иван6",
                    text: "Текст комментария6"
                },
                {
                    author: "Иван7",
                    text: "Текст комментария7"
                },
                {
                    author: "Иван8",
                    text: "Текст комментария8"
                },
                {
                    author: "Иван9",
                    text: "Текст комментария9"
                },
                {
                    author: "Иван10",
                    text: "Текст комментария10"
                },
                {
                    author: "Иван11",
                    text: "Текст комментария11"
                },
                {
                    author: "Иван12",
                    text: "Текст комментария12"
                },
                {
                    author: "Иван13",
                    text: "Текст комментария13"
                },
                {
                    author: "Иван14",
                    text: "Текст комментария14"
                },
                {
                    author: "Иван15",
                    text: "Текст комментария15"
                },
                {
                    author: "Иван16",
                    text: "Текст комментария16"
                },
                {
                    author: "Иван17",
                    text: "Текст комментария17"
                },
                {
                    author: "Иван18",
                    text: "Текст комментария18"
                },
                {
                    author: "Иван19",
                    text: "Текст комментария19"
                },
                {
                    author: "Иван20",
                    text: "Текст комментария20"
                }
            ];

            $scope.toggleSettingsCollapse = function() {
                $scope.isSettingsCollapsed = !$scope.isSettingsCollapsed;
            };

            var i = 21;
            $scope.myPagingFunction = function() {
                console.log("myPagingFunction");
                for (j=0;j<=30;j++) {
                    $scope.comments.push({
                        author: "Иван" + i,
                        text: "Текст комментария" + i
                    });
                    i++;
                }
            };

        }]);
