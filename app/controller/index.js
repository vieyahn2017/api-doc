/**
 ** yanghao 2017-7-14.
 */

function indexController($scope, $http, $window){
    var base_url = get_base_url();
    $http.get(base_url + "cc/api/category").success(function(data){
        $scope.typeList = data.rows;
    });

    $scope.remove_href = function(href){
        $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
        $http.delete(base_url + "cc/api/category?href=" + href
            ).success(function (data) {
                $window.location.reload();
                //$location.path("/");
            }).error(function (data, status, headers, config) {
                alert("delete failed");
                console.log(arguments);
            });
    };

    $scope.remove = function(target) {
        if(!confirm("确认删除")) {
            return;
        }
        $scope.remove_href(target.href);
    };
}

