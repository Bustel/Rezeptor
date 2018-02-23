let app = angular.module('app', []);

app.directive('customOnChange', function() {
  return {
    restrict: 'A',
    link: function (scope, element, attrs) {
      let onChangeHandler = scope.$eval(attrs.customOnChange);
      element.on('change', onChangeHandler);
      element.on('$destroy', function() {
        element.off();
      });

    }
  };
});

app.controller('RecipeController', ['$scope','$http', function ($scope,$http) {

    let recipeCtrl = this;

    recipeCtrl.recipe = {
        id: null,
        name: null,
        ingredients: [],
        steps: [],
        image: 'uploads/default.png'
    };

    recipeCtrl.edit = false;

    recipeCtrl.get_recipe = function (id) {
        let url = new URL(location.protocol + '//' + location.host + "/api/recipe"),
        params = {id: id};
        Object.keys(params).forEach(function (key) {url.searchParams.append(key, params[key])});

        if (id == null){
            recipeCtrl.edit = true;
            recipeCtrl.NameText = 'New Recipe';
            return
        }

        $http.get(url.toString()).then(function (response) {
            recipeCtrl.recipe.id = response.data.id;
            recipeCtrl.recipe.name = response.data.name;
            recipeCtrl.recipe.ingredients = response.data.ingredients;
            recipeCtrl.recipe.steps = response.data.steps;
            recipeCtrl.recipe.image = response.data.image;
            recipeCtrl.NameText = recipeCtrl.recipe.name;
        }).catch(reason => console.log(reason))

    };

    recipeCtrl.addStep = function () {
        let nr = 1;
        if (recipeCtrl.recipe.steps.length > 0) {
            nr = Math.max.apply(Math,recipeCtrl.recipe.steps.map(s => {return s.nr;})) + 1;
        }
        recipeCtrl.recipe.steps.push({description: recipeCtrl.stepText, nr: nr});
        recipeCtrl.stepText = "";
    };

    recipeCtrl.removeStep = function (index) {
        recipeCtrl.recipe.steps.splice(index,1);
        for (let i = index; i < recipeCtrl.recipe.steps.length; i ++){
            recipeCtrl.recipe.steps[i].nr -= 1;
        }
    };

    recipeCtrl.addIngredient = function () {
        let url = new URL(location.protocol + '//' + location.host + "/api/ingredient"),
        params = {name: recipeCtrl.ingrName};
        Object.keys(params).forEach(function (key) {url.searchParams.append(key, params[key])});

        $http.get(url.toString()).then(response => {
            if (!response.data.hasOwnProperty('id')){
                let req = {
                     method: 'POST',
                     url: '/api/ingredient',
                     headers: {
                       'Content-Type': 'application/json'
                     },
                     data: { name: recipeCtrl.ingrName }
                };
                return $http(req)
            } else {
                return response.data.id
            }
        }).then(result => {
            if (typeof (result) === "number"){
                recipeCtrl.recipe.ingredients.push({
                   ingredient: result,
                   name: recipeCtrl.ingrName,
                   unit: recipeCtrl.ingrUnit,
                   quantity: recipeCtrl.ingrAmount
                });
            } else {
                recipeCtrl.recipe.ingredients.push({
                   ingredient: result.data.id,
                   name: recipeCtrl.ingrName,
                   unit: recipeCtrl.ingrUnit,
                   quantity: recipeCtrl.ingrAmount
                });
            }
            recipeCtrl.ingrAmount = "";
            recipeCtrl.ingrName = "";
            recipeCtrl.ingrUnit = "";
        }).catch(reason => console.log(reason))
    };

    recipeCtrl.saveRecipe = function () {
        recipeCtrl.recipe.name = recipeCtrl.NameText;

        let method = 'POST';
        if (recipeCtrl.recipe.id != null){
            method = 'PUT';
        }

        let req = {
            method: method,
            url: '/api/recipe',
            headers: {
                'Content-Type': 'application/json'
            },
            data: recipeCtrl.recipe
        };
        $http(req).then(response => {
            recipeCtrl.recipe.id = response.data.id;
            recipeCtrl.recipe.name = response.data.name;
            recipeCtrl.recipe.ingredients = response.data.ingredients;
            recipeCtrl.recipe.steps = response.data.steps;
            recipeCtrl.edit = false;
        }).catch(reason => console.log(reason))
    };

    recipeCtrl.abortEdit = function () {
        if (confirm('Are you sure? All unsaved changes will be lost!')){
            if (recipeCtrl.recipe.id != null){
                recipeCtrl.edit = false;
                recipeCtrl.get_recipe(recipeCtrl.recipe.id);

            } else {
                location.reload()
            }
        }
    };

    recipeCtrl.deleteRecipe = function () {
        if (confirm('Do you really want to delete this recipe? This cannot be undone!')){
            if (recipeCtrl.recipe.id != null){
                req = {
                    method: 'DELETE',
                    url: '/api/recipe',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    data: { id: recipeCtrl.recipe.id}
                };
                $http(req).then(response => {
                    location.href = '/';
                }).catch(reason => {console.log(reason)})
            }
        }
    };
    
    $scope.previewImage = function (event) {
        let fileLst = event.target.files;
        if (fileLst.length > 0){
            let fileReader = new FileReader();
            let file = fileLst[0];

            if (file.type === 'image/jpeg' || file.type === 'image/png'){
                fileReader.addEventListener('load', () => {
                    let img = document.getElementById('recipePicture');
                    let r = fileReader.result;

                    img.src = r;
                    recipeCtrl.image = r;

                }, false);
                fileReader.readAsDataURL(file)
            } else {
                console.log('Wrong mime-type')
            }
        }

    }



    
}]);