let app = angular.module('app', []);
app.controller('mainViewController', function ($http) {
    let mainCtrl = this;
    mainCtrl.recipes = [];


    mainCtrl.get_recipes = function () {
        console.log('get recipes');
        $http.get('/api/latest').then(response => {
            mainCtrl.recipes = response.data;
        }).catch(reason => console.log(reason))
    }
});
