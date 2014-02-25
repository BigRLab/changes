(function(){
  'use strict';

  define(['app'], function(app) {
    app.controller('jobLogDetailsCtrl', [
        '$scope', '$rootScope', 'initialJob', 'initialBuildLog', '$window', '$timeout', '$http', '$stateParams', 'stream', 'flash',
        function($scope, $rootScope, initialJob, initialBuildLog, $window, $timeout, $http, $stateParams, Stream, flash) {
      var stream,
          logChunkData = {
            text: '',
            size: 0,
            nextOffset: 0
          },
          entrypoint = '/api/0/jobs/' + $stateParams.job_id + '/logs/' + $stateParams.source_id + '/';

      function updateBuildLog(data) {
        var $el = $('#log-' + data.source.id + ' > .build-log'),
            source_id = data.source.id,
            chars_to_remove, lines_to_remove,
            frag;

        if (data.offset < logChunkData.nextOffset) {
          return;
        }
        logChunkData.nextOffset = data.offset + data.size;

        frag = document.createDocumentFragment();

        // add each additional new line
        $.each(data.text.split('\n'), function(_, line){
          var div = document.createElement('div');
          div.className = 'line';
          div.innerHTML = line;
          frag.appendChild(div);
        });

        logChunkData.text += data.text;
        logChunkData.size += data.size;

        $el.append(frag);
      }

      function updateTestGroup(data) {
        $scope.$apply(function() {
          var updated = false,
              item_id = data.id,
              attr, result, item;

          // TODO(dcramer); we need to refactor all of this logic as its repeated in nealry
          // every stream
          if ($scope.testGroups.length > 0) {
            result = $.grep($scope.testGroups, function(e){ return e.id == item_id; });
            if (result.length > 0) {
              item = result[0];
              for (attr in data) {
                // ignore dateModified as we're updating this frequently and it causes
                // the dirty checking behavior in angular to respond poorly
                if (item[attr] != data[attr] && attr != 'dateModified') {
                  updated = true;
                  item[attr] = data[attr];
                }
                if (updated) {
                  item.dateModified = data.dateModified;
                }
              }
            }
          }
          if (!updated) {
            $scope.testGroups.unshift(data);
          }

          if (data.result.id == 'failed') {
            if ($scope.testFailures.length > 0) {
              result = $.grep($scope.testFailures, function(e){ return e.id == item_id; });
              if (result.length > 0) {
                item = result[0];
                for (attr in data) {
                  // ignore dateModified as we're updating this frequently and it causes
                  // the dirty checking behavior in angular to respond poorly
                  if (item[attr] != data[attr] && attr != 'dateModified') {
                    updated = true;
                    item[attr] = data[attr];
                  }
                  if (updated) {
                    item.dateModified = data.dateModified;
                  }
                }
              }
            }
            if (!updated) {
              $scope.testFailures.unshift(data);
            }
          }
        });
      }

      $scope.project = initialJob.data.project;
      $scope.build = initialJob.data.build;
      $scope.job = initialJob.data.job;
      $scope.logSource = initialBuildLog.data.source;

      $rootScope.activeProject = $scope.project;

      $timeout(function(){
        $.each(initialBuildLog.data.chunks, function(_, chunk){
          updateBuildLog(chunk);
        });
      });

      stream = new Stream($scope, entrypoint);
      stream.subscribe('buildlog.update', updateBuildLog);
    }]);
  });
})();
