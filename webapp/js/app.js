angular.module('reChat',
    [
        'reChat.feedCtrl',
        'reChat.chatCtrl',
        'reChat.headerCtrl',
        'ngRoute',
        'infinite-scroll',
        'ui.bootstrap'
    ]).config(['$routeProvider',
        function($routeProvider) {
            $routeProvider.
                when('/chat', {
                    templateUrl: 'templates/chat.html',
                    controller: 'ChatCtrl'
                }).
                when('/feed', {
                    templateUrl: 'templates/feed.html',
                    controller: 'FeedCtrl'
                }).
                otherwise({
                    redirectTo: '/feed'
                });
        }]);
