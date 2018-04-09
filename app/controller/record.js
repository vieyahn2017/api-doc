/**
 * yanghao 2017-7-14.
 */
function recordController($scope, $http, $location, $routeParams) {

    var base_url = get_base_url();
    var json = "data/type.json";

    var href = $routeParams.href;
    var id = $routeParams.id;
    $scope.href = href;
    $http.get(base_url + "m/api/record?href=" + href).success(function (data) {
        $scope.recordList = data.rows;
        console.log($scope.recordList);
        if($scope.recordList.length) {
            var current_api_id = $scope.recordList[0].RecordApiIdList[0];
            if(current_api_id) {
                $http.get(base_url + "m/api/record_api?id=" + current_api_id).success(function (data) {
                    $scope.current_api = data.rows[0];
                }).error(function(){
                   //
                });
            }
        }
    }).error(function(){
        $scope.recordList = [];
    });




    $scope.update_version = function () {
        $http.defaults.headers.post["Content-Type"] = "application/x-www-form-urlencoded";
        $http.put(base_url + "m/api/record?href=" + href, angular.toJson($scope.current_api, true)
            ).success(function (data) {
                //
            }).error(function (data, status, headers, config) {
                console.log(arguments);
            });
    };

}
