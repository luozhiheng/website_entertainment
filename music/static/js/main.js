var AlbumListPage = {
    init: function () {
        this.render();
        this.bindEvents();
    },

    render: function () {

    },

    bindEvents: function () {
        $('.albums-container .btn-favorite').on('click', function (e) {
            e.preventDefault();
            var self = $(this);
            var url = $(this).attr('href');
            $.getJSON(url, function (result) {
                if (result.success) {
                    $('.glyphicon-star', self).toggleClass('active')
                    }
                });
            return false
        })
    }
};

var SongListPage = {
    init: function () {
        this.render();
        this.bindEvents();
    },

    render: function () {
        $()
    },

    bindEvents: function () {
        $('.songs-container .btn-favorite').on('click', function (e) {
            e.preventDefault();
            var self = $(this);
            var url = $(this).attr('href');
            $.getJSON(url, function (result) {
                if (result.success) {
                    $('.glyphicon-star', self).toggleClass('active')
                }
            });
            return false
        })
    }
};
//TODO ���������б�
var Playlist = {
    init: function () {

    }
};


var TableFun = {
    init:function () {
        this.render();
        this.collapes();
    },
    render:function () {

    },
    collapes: function () {

        $('.songs-container').find('th').on('click', function (e) {
            var self = $(this);
            var $tablesel=self.parents('.table');

            $tablesel.find('tbody').find('tr').each(function () {
                $(this).fadeToggle('slow')
            });
        });

        $('.albums-container').find('.user-background').on('click', function (e) {

            var self = $(this);
            var id=self.attr('id');
            var idalbum="albums"+id;
            $('#'+idalbum).fadeToggle('slow');
        });
    }
};

var ToTop={
    init:function () {
     this.bindEvent()
    },

    render:function () {

    },

    bindEvent:function () {
         // �����������жϰ�ť��ʾ������
        $(window).on('scroll',function() {
            if ($(this).scrollTop() > 150) {
                $('.back-to-top').fadeIn(100);
            } else {
                $('.back-to-top').fadeOut(100);
            }
        });

        // jQueryʵ�ֶ�������
        $('.back-to-top').click(function(e) {
            e.preventDefault();
            $('html, body').animate({scrollTop: 0}, 500);
        })
    }
};



$(document).ready(function () {
    AlbumListPage.init();
    SongListPage.init();
    TableFun.init();
    ToTop.init()
});