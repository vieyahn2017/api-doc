/**
 ** yanghao 2017-7-14.
 */

function apiController($scope, $http, $q, $routeParams, $location, $window, $anchorScroll, $timeout, clipboard) {

    var href = $routeParams.href;
    $scope.href = href;
    $scope.base_url = get_base_url();

    $scope.show_api_list = function () {
        // $http.get($scope.base_url + "m/api?desc=true&href=" + href).success(function(data){  //添加的时候倒序方便点
        $http.get($scope.base_url + "m/api?href=" + href).success(function(data){
            //console.log(data.rows);
            var apiListTemp = data.rows;
            for(var i = 0; i < apiListTemp.length; i++) {
                api_extend_fn(apiListTemp[i]);
            }
            $scope.apiList = apiListTemp;
            console.log($scope.apiList);
            $timeout(function(){
                var id = $routeParams.id;
                $scope.scrollTo(id);
            });
        }).error(function(){
            $scope.apiList = [];
        });
    };

    $scope.show_api_list();


    var api_extend_fn = function (api) {
        //console.log(api);
        var paramsList = api.paramsList;
        for(var i = 0; i < paramsList.length; i++) {
            var skip = 0;
            if(paramsList[i].children.length > 0) {
                for(var j = 0; j < paramsList[i].children.length; j++) {
                    var item = paramsList[i].children[j];
                    paramsList.splice(i + 1, 0, item); // splice(i, 0, item) i处，增加item, 0是删除0个元素
                    //console.log(paramsList[i+1] == item); //3.27 这边splice进去的item，应该和item是同一个对象？
                }
                skip = paramsList[i].children.length + 1;
            }
            i += skip;
            // if(i>20) break;
        }
        var responseList = api.responseList;
        for(var i = 0; i < responseList.length; i++) {
            var skip = 0;
            if(responseList[i].children.length > 0) {
                for(var j = 0; j < responseList[i].children.length; j++) {
                    var item = responseList[i].children[j];
                    responseList.splice(i + 1, 0, item); // splice(i, 0, item) i处，增加item, 0是删除0个元素
                }
                skip = responseList[i].children.length + 1;
            }
            i += skip;
            // if(i>20) break;
        }
        //console.log(api);
        return api;
    }

    /*
    $http.get($scope.base_url + "m/api/authenticated").success(function(data){
        if(data.code == 1) {
            $scope.authenticated = true;
        } else if (data.code == -1) {
            $scope.authenticated = false;
        }
        //console.log($scope.authenticated);
    }).error(function(){
        $scope.authenticated = false;
    });
    */
    // $scope.authenticated = is_authenticated($scope, $http);

    $scope.authenticated = is_authenticated();
    $scope.show_edit = $scope.authenticated;
    $scope.testing = is_testing();

    var uuid = function () {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
            return v.toString(16);
        });
    };

    var param_demo = function(param_name) {
        var name = "param";
        if(param_name) {
           name = param_name;
        }
        return {
            "name": name,
            "default": "",
            "required": "false",
            "type_": "string",
            "description": "",
            "_id": uuid(),
            "children": [],
            "parent_id": null,
            "category_href": href
        }
    };
    var json_sub_param_demo = function(parent_id) {
        var param = param_demo();
        param.name = "json_param";
        param.parent_id = parent_id;
        return param;
    };
    var empty_api = {
        "_id": "-1",
        "name": "接口名",
        "url": "/url",
        "method": "GET",
        "description": "接口描述",
        "paramsList": [
            param_demo()
        ],
        "responseList":[
            param_demo()
        ],
        "requestUrlDemo": "\\",
        "requestParamsDemo": "",
        "responseDemo": "{\n    \"msg\": \"\", \n    \"result\": {},  \n    \"code\": 1\n}",
        "category_href": href
    };

    //$scope.clipboard_api = angular.copy(empty_api);
    //$scope.clipboard_params = [param_demo()];
    $scope.clipboard_api = null;
    $scope.clipboard_params = null;

    $scope.TYPES = [
        "string", "int", "boolean", "list", "json"
    ];
    $scope.METHODS = [
        "GET", "POST", "PUT", "DELETE"
    ];


    $scope.add = function(){
        $scope.current = angular.copy(empty_api);
        $scope.isNew = true;
    };
    $scope.edit = function(api_item) {
        $scope.current = api_item;
        $scope.isNew = false;
    };

    var check_unique_un = function(new_item){
        /* $scope.isUnique没法传递返回，难不成绑定过程，与$http的方法不同步。 也没法在$http.success里面return，那是闭包
         *  api.html 里面把div id="{{item.name}} 改成了 div id="{{item._id}}
         */
        $scope.isUnique = true;
        $http.get($scope.base_url + "m/api/exist?name=" + new_item.name + "&href=" + new_item.category_href
        ).success(function (data) {
                //console.log(data.code == 1);  //true
                //console.log(data.code == '1'); //true
                if(data.code == 1) {
                    $scope.isUnique = false;
                } else if (data.code == -1) {
                    $scope.isUnique = true;
                }
            }).error(function (data, status, headers, config) {
                console.log(arguments);
            });
        return $scope.isUnique;
    };
    var check_unique = function(new_item){
        return true;
    };

    $scope.save_api = function(current_item){
        console.log(current_item);
        if($scope.apiForm.$invalid) {
            return;
        }
        $scope.isUnique = true;
        var r = check_unique(current_item);
        //console.log(r);
        if(!r) {
            alert("接口名重复了，重新起一个吧");
            return;
        } else {
            //console.log("接口名可用：" + current_item.name);
        }

        if($scope.isNew) {
            $scope.save_me_yh(current_item);
            $scope.save_record(current_item, "save");
        }
        else {
            $scope.update_me_yh(current_item);
            $scope.save_record(current_item, "update");
        }
    };

    $scope.save_me_yh = function(new_item){ //yh
        $scope.save_api_item = new_item;
        $scope.save_api_item.temp_api_ids = [];

        var post_paramsList = function() {
            var deferred = $q.defer();
            $http.post($scope.base_url + "m/api/param",
                angular.toJson(new_item.paramsList, true)
            ).success(function (data) {
                    $scope.save_api_item.paramsIdList = data.rows.param_ids;
                    $scope.save_api_item.temp_api_ids.push(data.rows.temp_api_id);
                    deferred.resolve($scope.save_api_item);
                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            return deferred.promise;
        };

        var post_responseList = function() {
            var deferred = $q.defer();
            $http.post($scope.base_url + "m/api/param",
                angular.toJson(new_item.responseList, true)
            ).success(function (data) {
                    $scope.save_api_item.responseIdList = data.rows.param_ids;
                    $scope.save_api_item.temp_api_ids.push(data.rows.temp_api_id);
                    deferred.resolve($scope.save_api_item);
                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            return deferred.promise;
        };

        $q.all([post_paramsList(), post_responseList()])
            .then(function(result){
                //console.log($scope.save_api_item);
                //console.log(result);
                $http.post($scope.base_url + "m/api",
                    angular.toJson($scope.save_api_item, true)
                ).success(function (data) {
                        //console.log(data.rows);
                        $scope.apiList.push(api_extend_fn(data.rows));
                        $scope.isNew = false;
                        $scope.current = null;
                        var scroll_id = data.rows._id;
                        $timeout(function(){
                            //console.log(scroll_id);
                            $scope.scrollTo(scroll_id);
                        });
                    }).error(function (data, status, headers, config) {
                        console.log(arguments);
                    });
            });
        //console.log($scope.save_api_item);
    };

    $scope.update_me_yh = function(update_item){ //yh
        $scope.save_api_item = update_item;

        var put_paramsList = function(api_id) {
            var deferred = $q.defer();
            $http.put($scope.base_url + "m/api/param",
                angular.toJson({"api_id": api_id, "rows": update_item.paramsList}, true)
            ).success(function (data) {
                    $scope.save_api_item.paramsIdList = data.rows;
                    deferred.resolve($scope.save_api_item);
                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            return deferred.promise;
        };

        var put_responseList = function(api_id) {
            var deferred = $q.defer();
            $http.put($scope.base_url + "m/api/param",
                angular.toJson({"api_id": api_id, "rows": update_item.responseList}, true)
            ).success(function (data) {
                    $scope.save_api_item.responseIdList = data.rows;
                    deferred.resolve($scope.save_api_item);
                }).error(function (data, status, headers, config) {
                    console.log(arguments);
                });
            return deferred.promise;
        };

        $q.all([put_paramsList(update_item._id), put_responseList(update_item._id)])
            .then(function(result){
                //console.log($scope.save_api_item);
                //console.log(result);
                $http.put($scope.base_url + "m/api",
                    angular.toJson($scope.save_api_item, true)
                ).success(function (data) {
                        //console.log(data.rows);
                        //angular.extend($scope.edit_api_item, api_extend_fn(data.rows));
                        //这一句浅拷贝，对页面当前自动更新尤为关键
                        $scope.isNew = false;
                        $scope.current = null;
                        var scroll_id = $scope.save_api_item._id;
                        $timeout(function(){
                            $scope.scrollTo(scroll_id);
                        });
                    }).error(function (data, status, headers, config) {
                        console.log(arguments);
                    });
            });
        //console.log($scope.save_api_item);
    };

    $scope.cancel = function(){
        $scope.isNew = false;
        $scope.current = null;
    };

    $scope.editorOptions = {
        lineNumbers: true,
        matchBrackets: true,
        mode: "application/x-httpd-php",
        indentUnit: 4,
        indentWithTabs: true,
        enterMode: "keep",
        tabMode: "shift",
        onLoad: function(){
            console.log(123);
        }
    };

    $scope.scrollTo = function(id){
        var old = $location.hash();
        $location.hash(id);
        $anchorScroll();
        //reset to old to keep any additional routing logic from kicking in
        $location.hash(old);
    };

    $scope.add_param = function(collection){
        var param = param_demo();
        collection.push(param);
    };

    $scope.add_json_param_children = function(collection, item){
        //增加只能末位添加的检查
        var pos = collection.length - 1;
        do {
            var t = collection[pos];
            if(!t.parent_id) {  // !t.parent_id && t.type_ =='json'
                break;
            }
            pos -= 1;
        } while (pos >= 0);
        //console.log(collection.length);
        //console.log(pos);
        //console.log(collection.indexOf(item));
        if(collection.indexOf(item) != pos) {
            alert('只能在末位json param新增子项');
            return;
        }
        var sub_param = json_sub_param_demo(item._id);
        item.children.push(sub_param);
        collection.push(sub_param);
        // 上面push的是同一个对象，所以同时更新；
        // 但是如果是用下面这种方式，肯定就不同时更新了
        // var copy = angular.copy(sub_param);
        // collection.push(copy);
    };

    var remove_i = function(collection, item){
        for(var i = 0; i < collection.length; i++) {
            if(collection[i] == item) {
                collection.splice(i, 1);  // 在i处删除1个元素
                break;
            }
        }
    };

    $scope.remove_param = function(collection, item){
        if(confirm("确认删除param?")) {
            if (item.type_ == 'json' && item.children.length) {
                if(confirm("该param有子元素，请再次确认删除param?")) {
                    // 1.
                    remove_i(collection, item);
                    // 2.
                    for(var i = 0; i < collection.length; i++) {
                        if(collection[i].parent_id == item._id) {
                            remove_i(collection, collection[i]);
                            i--;
                            //这种用collection.length作为循环条件，但是在内部因为splice的操作，导致循环条件动态变化，并不符合真正的编程科学...
                        }
                    }
                }
            } else {
                remove_i(collection, item);
            }


        }
    };
    $scope.remove_json_param_children = function(collection, item){
        if(confirm("确认删除param??")) {
            // 1.
            remove_i(collection, item);
            // 2.
            for(var i = 0; i < collection.length; i++) {
                if(collection[i]._id == item.parent_id) {
                    remove_i(collection[i].children, item);
                    break;
                }
            }
        }
    };

    $scope.remove_api = function(item){
        //  <button ng-show="show_edit" class="btn btn-danger btn-xs pull-right" style="margin-right: 5px;" ng-click="remove(apiList, item); save_me();">delete</button>
        if(confirm("确认删除api?")) {
            $http.delete($scope.base_url + "m/api?id=" + item._id
            ).success(function (data) {
                    $window.location.reload();
                }).error(function (data, status, headers, config) {
                    alert("delete failed");
                    console.log(arguments);
                });
        }
    };


    $scope.back = function(){
        $scope.scrollTo("top");
    };

    $scope.log = function(current_item, current_param){
        console.log(current_item);
        if(current_param) {
            console.log(current_param);
        }
    };

    var is_param_equal = function(param1, param2) {
        // return param1._id == param2._id;
        for (k in param1) {
            if (param1[k] != param2[k]) {
                return false;
            }
        }
        return true;
    };

    $scope.assert_children_equal = function(collection, item){

        if(item.type_ != 'json') {
            console.log("item is not json.");
            return false;
        }
        var len = item.children.length;
        if(!len) {
            console.log("item's children is empty.");
            return false;
        }
        var pos = collection.indexOf(item);
        if(pos == -1) {
            console.log("item is not in collection.");
            return false;
        }

        console.log(collection.slice(pos + 1, pos + 1 + len));
        console.log(item.children);

        for(var i = 0; i < len; i++) {
            //collection[pos + 1 + i] ~~ item.children[i] 顺序不是一一对应的，只能挨个迭代。
            //is_param_equal(collection[pos + 1 + i], item.children[i]) 这样行不通
            var foo = collection[pos + 1 + i];
            for(var j = 0; j < len; j++) {
                if(item.children[j]._id == foo._id) {
                    var equal_ = is_param_equal(foo, item.children[j]);
                    if(equal_) {
                        break; //判断下一个子元素
                    } else {
                        console.log(foo);
                        console.log(item.children[j]);
                        return false;
                    }
                }
            }
        }

        console.log("is equal by validate");
    };

    $scope.make_param_demo = function(collection) {

        var _chose = function(item) {
            return function(item, type) {
                switch (type) {
                    case 'int':
                        return item.default || 0;
                    case 'string':
                        return item.default || "";
                    case 'boolean':
                        return item.default || false;
                    case 'list':
                        return item.default || [];
                    case 'json':
                        return item.default || {};
                    default:
                        return item.default || "";
                }
            }(item, item.type_);
        };

        var result = {};
        for (var i = 0; i < collection.length; i++){
            var item = collection[i];
            var key = item.name;
            if(result.hasOwnProperty(key)){
                key = key + '~' + i;
            };
            if(item.parent_id) {
                continue;
            }
            if(item.type_ != 'json') {
                result[key] = _chose(item);
            } else if(item.type_ == 'json') {
                var obj = {};
                if(item.children.length) {
                    for (var j = 0; j < item.children.length; j++){
                        var obj_key = item.children[j].name;
                        if(obj.hasOwnProperty(obj_key)){
                            obj_key = obj_key + '~' + j;
                        };
                        obj[obj_key]  = _chose(item.children[j]);
                    }
                }
                result[key] = obj;
            }
        }

        var str = JSON.stringify(result, null, 4);
        return str;
    }


    $scope.make_url_demo = function(url, collection) {

        // url 没有json和子属性这么复杂的情况, 所以_chose也简化些
        var _chose = function(item) {
            return function(item, type) {
                switch (type) {
                    case 'int':
                        return item.default || 0;
                    case 'boolean':
                        return item.default || false;
                    case 'string':
                        return item.default || "";
                    default:
                        return item.default || "";
                }
            }(item, item.type_);
        };

        // key_in_path, such as <id>
        var key_in_path = null;
        var _re_ids = url.match(/<[\w]+>/);
        if(_re_ids && _re_ids[0]) {
            key_in_path = _re_ids[0];
            key_in_path = key_in_path.substring(1, key_in_path.length - 1);
        }

        var param_filters = "?";
        for (var i = 0; i < collection.length; i++){
            var item = collection[i];
            if(item.parent_id) {
                continue;
            }
            var key = item.name;
            if(key==key_in_path) {
                url = url.replace("<" + key_in_path + ">", "<" + _chose(item) + ">");
                continue;
            }
            var value = _chose(item);
            param_filters += key + '=' + value + '&';
        }

        param_filters = param_filters.substring(0, param_filters.length - 1);
        return url + param_filters;
    }

    $scope.copy_api = function (current) {
        if (!clipboard.supported) {
            console.log('Sorry, copy to clipboard is not supported');
            return;
        }
        // 这个是可用的，把内容确实拷贝进了clipboard，
        clipboard.copyText(JSON.stringify(current, null, 4));
        // 但是目前怎么用clipboard组件传递到前端，没弄清。还是用$scope绑定变量传递吧。
        // 目前这种方式，不能跨分类粘贴，所以局限性很大。
        $scope.clipboard_api = angular.copy(current);
    };

    var check_api_before_paste = function (api) {
        var result = {"validity": false, "msg": ""};
        if(!api) {
            return result;
        }
        if(!api.hasOwnProperty("_id")){return result;}
        if(!api.hasOwnProperty("name")){return result;}
        if(!api.hasOwnProperty("url")){return result;}
        if(!api.hasOwnProperty("paramsList")){return result;}
        if(!api.hasOwnProperty("responseList")){return result;}
        if(!api.hasOwnProperty("method")){return result;}
        result.validity = true;
        result.msg = "name=" + api.name + ", url=" + api.url;
        return result;
    };

    $scope.paste_api = function (api_id) {
        //console.log(JSON.stringify($scope.clipboard_api, null, 4));
        var result = check_api_before_paste($scope.clipboard_api);
        if(result.validity) {
            if(confirm("确认粘贴api? " + result.msg)) {
                if(api_id && api_id != -1) {
                    // POST的_id可以不管， PUT的_id必须使用之前的_id
                    $scope.clipboard_api._id = api_id;
                }
                return $scope.clipboard_api;
            }
        } else {
            var copy = angular.copy(empty_api);
            copy.name = "api_paste_fail_demo";
            return copy;
        }
    };

    $scope.copy_params = function (collection) {
        if (!clipboard.supported) {
            console.log('Sorry, copy to clipboard is not supported');
            return;
        }
        console.log(JSON.stringify(collection, null, 4));

        var newCollection = angular.copy(collection);
        // @必须换掉每个param的_id
        //先全部换id，从根元素param到json的children-param;  //再把children里面的换成对应的
        var json_id_map = {};
        var children_id_item_map = {};
        for(var i = 0; i < newCollection.length; i++) {
            var item = newCollection[i];
            var old_id = item._id;
            var new_id = uuid();
            item._id = new_id;
            if(item.type_ == 'json' && item.children.length) {
                json_id_map[old_id] = new_id;
            }
            if(item.parent_id) {
                // 换parent_id，应该不存在子元素还排在前面的情况
                item.parent_id = json_id_map[item.parent_id];
                children_id_item_map[old_id] = item;
            }
        }
        for(var i = 0; i < newCollection.length; i++) {
            var item = newCollection[i];
            if(item.type_ == 'json' && item.children.length) {
                for(var j = 0; j < item.children.length; j++) {
                    var child = item.children[j];
                    item.children[j] = children_id_item_map[child._id];
                }
            }
        }
        clipboard.copyText(JSON.stringify(newCollection, null, 4));
        $scope.clipboard_params = newCollection;
        return $scope.clipboard_params;
    };

    var check_params_before_paste = function (bars) {
        var result = {"validity": false, "items": []};
        if(!bars) {
            return result;
        }
        if(bars instanceof Array) {
            for(var i = 0; i < bars.length; i++) {
                var bar = bars[i];
                //for (var key in bar) { console.log(key); console.log(bar[key]); }  //遍历
                if(i == 0) {
                    //简化工作量：就对第一项校验即可。
                    if(!bar.hasOwnProperty("name")){break;}
                    if(!bar.hasOwnProperty("default")){break;}
                    if(!bar.hasOwnProperty("type_")){break;}
                    if(!bar.hasOwnProperty("_id")){break;}
                    if(!bar.hasOwnProperty("children")){break;}
                    if(!bar.hasOwnProperty("parent_id")){break;}
                }
                result.items.push(bar.name);
            }
            if(result.items.length) {
                result.validity = true;
            }
        }
        return result;
    };

    $scope.paste_params = function (api_id) {
        //console.log(JSON.stringify($scope.clipboard_params, null, 4));
        var result = check_params_before_paste($scope.clipboard_params);
        //console.log(result);
        if(result.validity) {
            if(confirm("确认粘贴params? 包括：" + result.items.toString())) {
                if(!api_id && api_id != -1) {
                    api_id = -1;
                }
                // POST的_id可以不管， PUT的_id必须使用之前的_id
                for(var i= 0; i < $scope.clipboard_params.length; i++){
                    $scope.clipboard_params[i].api_id = api_id;
                }
                return $scope.clipboard_params;
            }
        } else {
            return [param_demo(), param_demo("param~2")];
        }
    };


    $scope.save_record = function(new_item, method){

        var record_api = {
            "name": method,
            "api_id": new_item._id,
            "category_href": new_item["category_href"],
            "content": JSON.stringify(new_item, null, 4)
        };

        $http.post($scope.base_url + "m/api/record/api",
            angular.toJson(record_api, true)
        ).success(function (data) {
                var record = {
                    "name": method + new_item._id,
                    "version": null,
                    "category_href": new_item["category_href"],
                    "RecordApiIdList": data.rows,
                };
                $http.post($scope.base_url + "m/api/record",
                    angular.toJson(record, true)
                ).success(function (data) {
                        console.log(data);
                    }).error(function (data, status, headers, config) {
                        console.log(arguments);
                    });
            }).error(function (data, status, headers, config) {
                console.log(arguments);
            });
        return $scope.isUnique;
    };


}

