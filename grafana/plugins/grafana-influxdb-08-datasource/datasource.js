define([
  'angular',
  'lodash',
  'app/core/utils/datemath',
  './influx_series',
  './query_builder',
  './query_ctrl',
  './func_editor',
],
function (angular, _, dateMath, InfluxSeries, InfluxQueryBuilder) {
  'use strict';

  var self;

  function InfluxDatasource(instanceSettings, $q, backendSrv, templateSrv) {
    this.urls = _.map(instanceSettings.url.split(','), function(url) {
      return url.trim();
    });

    this.username = instanceSettings.username;
    this.password = instanceSettings.password;
    this.name = instanceSettings.name;
    this.basicAuth = instanceSettings.basicAuth;

    this.q = $q;
    this.backendSrv = backendSrv;
    this.templateSrv = templateSrv;

    self = this;
  }

  InfluxDatasource.prototype.query = function(options) {
    var timeFilter = getTimeFilter(options);

    var promises = _.map(options.targets, function(target) {
      if (target.hide || !((target.series && target.column) || target.query)) {
        return [];
      }

      // build query
      var queryBuilder = new InfluxQueryBuilder(target);
      var query = queryBuilder.build();

      // replace grafana variables
      query = query.replace('$timeFilter', timeFilter);
      query = query.replace(/\$interval/g, (target.interval || options.interval));

      // replace templated variables
      query = self.templateSrv.replace(query, options.scopedVars);

      var alias = target.alias ? self.templateSrv.replace(target.alias, options.scopedVars) : '';

      var handleResponse = _.partial(handleInfluxQueryResponse, alias, queryBuilder.groupByField);
      return this._seriesQuery(query).then(handleResponse);

    }, this);

    return this.q.all(promises).then(function(results) {
      return { data: _.flatten(results) };
    });
  };

  InfluxDatasource.prototype.annotationQuery = function(options) {
    var timeFilter = getTimeFilter({rangeRaw: options.rangeRaw});
    var query = options.annotation.query.replace('$timeFilter', timeFilter);
    query = self.templateSrv.replace(query);

    return this._seriesQuery(query).then(function(results) {
      return new InfluxSeries({seriesList: results, annotation: options.annotation}).getAnnotations();
    });
  };

  InfluxDatasource.prototype.listColumns = function(seriesName) {
    seriesName = self.templateSrv.replace(seriesName);

    if(!seriesName.match('^/.*/') && !seriesName.match(/^merge\(.*\)/)) {
      seriesName = '"' + seriesName+ '"';
    }

    return this._seriesQuery('select * from ' + seriesName + ' limit 1').then(function(data) {
      if (!data) {
        return [];
      }
      return data[0].columns.map(function(item) {
        return /^\w+$/.test(item) ? item : ('"' + item + '"');
      });
    });
  };

  InfluxDatasource.prototype.listSeries = function(query) {
    // wrap in regex
    if (query && query.length > 0 && query[0] !== '/')  {
      query = '/' + query + '/';
    }

    return this._seriesQuery('list series ' + query).then(function(data) {
      if (!data || data.length === 0) {
        return [];
      }
      return _.map(data[0].points, function(point) {
        return point[1];
      });
    });
  };

  InfluxDatasource.prototype.testDatasource = function() {
    return this.metricFindQuery('list series').then(function () {
      return { status: "success", message: "Data source is working", title: "Success" };
    });
  };

  InfluxDatasource.prototype.metricFindQuery = function (query) {
    var interpolated;
    try {
      interpolated = this.templateSrv.replace(query);
    }
    catch (err) {
      return this.q.reject(err);
    }

    return this._seriesQuery(interpolated)
      .then(function (results) {
        if (!results || results.length === 0) { return []; }

        return _.map(results[0].points, function (metric) {
          return {
            text: metric[1],
            expandable: false
          };
        });
      });
  };

  function retry(deferred, callback, delay) {
    return callback().then(undefined, function(reason) {
      if (reason.status !== 0 || reason.status >= 300) {
        reason.message = 'InfluxDB Error: <br/>' + reason.data;
        deferred.reject(reason);
      }
      else {
        setTimeout(function() {
          return retry(deferred, callback, Math.min(delay * 2, 30000));
        }, delay);
      }
    });
  }

  InfluxDatasource.prototype._seriesQuery = function(query) {
    return this._influxRequest('GET', '/series', {
      q: query,
    });
  };

  InfluxDatasource.prototype._influxRequest = function(method, url, data) {
    var _this = this;
    var deferred = this.q.defer();

    retry(deferred, function() {
      var currentUrl = _this.urls.shift();
      _this.urls.push(currentUrl);

      var params = {
        u: _this.username,
        p: _this.password,
      };

      if (method === 'GET') {
        _.extend(params, data);
        data = null;
      }

      var options = {
        method: method,
        url:    currentUrl + url,
        params: params,
        data:   data,
        inspect: { type: 'influxdb' },
      };

      options.headers = options.headers || {};
      if (_this.basicAuth) {
        options.headers.Authorization = 'Basic ' + _this.basicAuth;
      }

      return _this.backendSrv.datasourceRequest(options).then(function(response) {
        deferred.resolve(response.data);
      });
    }, 10);

    return deferred.promise;
  };

  InfluxDatasource.prototype._getDashboardInternal = function(id) {
    var queryString = 'select dashboard from "grafana.dashboard_' + btoa(id) + '"';

    return this._seriesQuery(queryString).then(function(results) {
      if (!results || !results.length) {
        return null;
      }

      var dashCol = _.indexOf(results[0].columns, 'dashboard');
      var dashJson = results[0].points[0][dashCol];

      return angular.fromJson(dashJson);
    }, function() {
      return null;
    });
  };

  InfluxDatasource.prototype.getDashboard = function(id) {
    return this._getDashboardInternal(id).then(function(dashboard) {
      if (dashboard !== null)  {
        return dashboard;
      }
      throw "Dashboard not found";
    }, function(err) {
      throw  "Could not load dashboard, " + err.data;
    });
  };

  InfluxDatasource.prototype.searchDashboards = function() {
    var influxQuery = 'select * from /grafana.dashboard_.*/ ';
    return this._seriesQuery(influxQuery).then(function(results) {
      var hits = { dashboards: [], tags: [], tagsOnly: false };

      if (!results || !results.length) {
        return hits;
      }

      for (var i = 0; i < results.length; i++) {
        var dashCol = _.indexOf(results[i].columns, 'title');
        var idCol = _.indexOf(results[i].columns, 'id');

        var hit =  {
          id: results[i].points[0][dashCol],
          title: results[i].points[0][dashCol],
        };

        if (idCol !== -1) {
          hit.id = results[i].points[0][idCol];
        }

        hits.dashboards.push(hit);
      }
      return hits;
    });
  };

  function handleInfluxQueryResponse(alias, groupByField, seriesList) {
    var influxSeries = new InfluxSeries({
      seriesList: seriesList,
      alias: alias,
      groupByField: groupByField
    });

    return influxSeries.getTimeSeries();
  }

  function getTimeFilter(options) {
    var from = getInfluxTime(options.rangeRaw.from, false);
    var until = getInfluxTime(options.rangeRaw.to, true);
    var fromIsAbsolute = from[from.length-1] === 's';

    if (until === 'now()' && !fromIsAbsolute) {
      return 'time > ' + from;
    }

    return 'time > ' + from + ' and time < ' + until;
  }

  function getInfluxTime(date, roundUp) {
    if (_.isString(date)) {
      if (date === 'now') {
        return 'now()';
      }

      var parts = /^now-(\d+)([d|h|m|s])$/.exec(date);
      if (parts) {
        var amount = parseInt(parts[1]);
        var unit = parts[2];
        return 'now()-' + amount + unit;
      }

      date = dateMath.parse(date, roundUp);
    }
    return (date.valueOf() / 1000).toFixed(0) + 's';
  }

  return InfluxDatasource;
});
