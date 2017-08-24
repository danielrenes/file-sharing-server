var get_cookie = function(search_key) {
  let cookies = document.cookie.split(";")
  for (let i = 0; i < cookies.length; i++) {
    let [key, value] = cookies[i].split("=");
    while (key.charAt(0) == " ") {
      key = key.substring(1);
    }
    if (key == search_key) {
      return value == "null" ? null : value;
    }
  }
  return null;
};

var downloading = get_cookie("downloading");
var cached_on_server = [];

var set_cached = function(filename) {
  let current_cache_img = $("td.filename:contains(" + filename + ")").closest("tr").children("td.cached").children("img");
  let current_cache_img_src = current_cache_img.attr("src");
  let current_cache_img_src_splitted = current_cache_img_src.split("/");
  if (current_cache_img_src_splitted[current_cache_img_src_splitted.length - 1] == "no_cache.svg") {
    current_cache_img_src_splitted[current_cache_img_src_splitted.length - 1] = "cache.svg";
    current_cache_img.attr("src", current_cache_img_src_splitted.join("/"));
  }
}

var set_not_cached = function(filename) {
  let current_cache_img = $("td.filename:contains(" + filename + ")").closest("tr").children("td.cached").children("img");
  let current_cache_img_src = current_cache_img.attr("src");
  let current_cache_img_src_splitted = current_cache_img_src.split("/");
  if (current_cache_img_src_splitted[current_cache_img_src_splitted.length - 1] == "cache.svg") {
    current_cache_img_src_splitted[current_cache_img_src_splitted.length - 1] = "no_cache.svg";
    current_cache_img.attr("src", current_cache_img_src_splitted.join("/"));
  }
}

var check_download_finished = function(filename) {
  $.ajax({
    url: $SCRIPT_ROOT + '/finished_transfers',
    type: "GET",
    datatype: "html"
  }).done(function(data) {
    if (data.trim().length == 0) {
      setTimeout(check_download_finished, 2000);
    } else {
      $(document.body).append(data);
      set_cached(decodeURI(filename));
      downloading = null;
      document.cookie = "downloading=";
      setTimeout(function() {
        $("ul.flashes").empty();
        $("ul.flashes").remove();
      }, 2000);
    }
  });
};

var refresh_cache_info = function() {
  $.ajax({
    url: $SCRIPT_ROOT + "/cache_info",
    type: "GET",
    datatype: "json"
  }).done(function(data) {
    let currently_cached_on_server = JSON.parse(data)["cached"];
    currently_cached_on_server.forEach(function(element) {
      set_cached(element);
    });
    if (cached_on_server.length != 0) {
      cached_on_server.forEach(function(element) {
        if ($.inArray(element, currently_cached_on_server) == - 1) {
          set_not_cached(element);
        }
      });
    }
    cached_on_server = currently_cached_on_server;
  });
};

$(document).ready(function() {
  refresh_cache_info();
  setInterval(refresh_cache_info, 60000);

  $("td.download > a > img").click(function() {
    $this = $(this);
    if (downloading != null && downloading != "") {
      html_warning = [];
      html_warning.push("<p class='warning'>", "Downloading of another file is in progress. Try again when it finishes!", "</p>");
      $this.closest("tr").append(html_warning.join(""));
      setTimeout(function() {
        $("p.warning").remove();
      }, 2000);
      return false;
    } else {
      let filepath_splitted = $this.parent().attr("href").split("/");
      let filename = filepath_splitted[filepath_splitted.length - 1];
      document.cookie = "downloading=" + filename;
    }
  });

  if (downloading != null && downloading != "") {
    check_download_finished(downloading);
  }
});
