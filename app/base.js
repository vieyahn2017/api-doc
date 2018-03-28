function get_base_url() {
    host = "http://127.0.0.1:30000";
    base_url = host + "/api/v1/";
    return base_url;
}

function is_authenticated() {
    return true;
}

/*

function is_authenticated($scope, $http) {

    $http.get(get_base_url() + "m/api/authenticated").success(function(data){
        if(data.code == 1) {
            $scope.authenticated = true;
        } else if (data.code == -1) {
            $scope.authenticated = false;
        }
        console.log($scope.authenticated);
    }).error(function(){
        $scope.authenticated = false;
    });

    return $scope.authenticated;
}

*/
