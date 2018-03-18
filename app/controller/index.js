/**
 ** yanghao 2017-7-14.
 */

function indexController($scope, $http, $window){
    var base_url = get_base_url();
    $http.get(base_url + "m/api/category").success(function(data){
        $scope.typeList = data.rows;
    });

    $scope.remove_href = function(href){
        $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
        $http.delete(base_url + "m/api/category?href=" + href
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

    $scope.loop_icon = function(id) {
        // use font-awesome icons
        var fa_icon_list = [
            "fa-gear", "fa-globe", "fa-flag", "fa-fire",
            "fa-gift", "fa-laptop", "fa-leaf", "fa-map",
            "fa-plug", "fa-paw", "fa-ship", "fa-sitemap"];
        i = id % 12 ;
        return fa_icon_list[i];
    };

}

