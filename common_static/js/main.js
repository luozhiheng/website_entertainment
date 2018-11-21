var AlbumListPage={
    init:function () {
      this.render();
      this.bindEvents();
    },

    render:function () {

    },

    bindEvents:function () {
        $('.album-container .btn-favorite').on('click',function (e) {
            e.preventDefault();
            var self=$(this);
            var url=$(this).attr('href');
            $.getJSON(url,function (result) {
                if(result.success){
                    $('.glyphicon-star',self).toggleClass('active')
                }
            });

            return false
        })
    }
};

var SongListPage={
    init:function () {
      this.render();
      this.bindEvents();
    },

    render:function () {
    $()
    },

    bindEvents:function () {
        $('.song-container .btn-favorite').on('click',function (e) {
            e.preventDefault();
            var self=$(this);
            var url=$(this).attr('href');
            $.getJSON(url,function (result) {
                if(result.success){
                    $('.glyphicon-star',self).toggleClass('active')
                }
            });

            return false
        })
    }
};

var Playlist={
    init:function () {

    }
};

$(document).ready(function () {
   AlbumListPage.init();
   SongListPage.init()
});