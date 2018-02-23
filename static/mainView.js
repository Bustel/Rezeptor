fetch('/api/latest').then(function (response) {
    if (response.status !== 200){
        console.log('Unexpected HTTP Error! Code: ' + response.status);
        return;
    }
    response.json().then(function (data) {
        console.log(data);
        var recipeDiv = document.getElementById('recipes');
        for (var i = 0;i < data.length; i++){
            var cardDiv = document.createElement('div');
            var img = document.createElement('img');
            var containerDiv = document.createElement('div');

            cardDiv.classList.add('card');
            containerDiv.innerHTML  = data[i].name;
            containerDiv.classList.add('container');
            img.alt = 'Image of ' + data[i].name;
            img.style.width = '100%';
            img.src = data[i].image;


            cardDiv.appendChild(img);
            cardDiv.appendChild(containerDiv);
            recipeDiv.appendChild(cardDiv);

            var handler = function (index) {
              return function () {
                  window.location.assign('/recipe/' + data[index].id)
              }
            };
            cardDiv.addEventListener('click',handler(i))
        }

    }).catch(function (reason) {
        console.log(reason)
    });
}).catch(function (reason) {
    console.log('Beep Beep Beep: -S', reason)
});