//
//     Copyright (C) 2011 Loic Dachary <loic@dachary.org>
//
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, either version 3 of the License, or
//     (at your option) any later version.
//
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
//
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.
//
module("bug");

test("frame", function() {
    expect(3);

    var bugzilla_url = location.protocol + '//' + location.hostname;

    equal(location.href.indexOf(bugzilla_url), 0, bugzilla_url);

    $.bug.window = {
        top: 'something',
        parent: { bugzilla_url: bugzilla_url }
    };

    equal($.bug.url, '');
    equal($.bug.url, bugzilla_url);
    $.bug.url = '';
});

test("ajax", function() {
    expect(4);

    var status = 404;
    var statusText = 'Status text';
    var responseText = 'Error text';
    var ajax = $.ajax;
    $.ajax = function(settings) {
        return $.Deferred().reject({
            status: status,
            statusText: statusText,
            responseText: responseText
        });
    };

    try {
        $.bug.ajax('POST', 'DOESNOTEXIST', {});
    } catch(e) {
        ok($('.error').text().indexOf(status) >= 0, status);
        ok($('.error').text().indexOf(statusText) >= 0, statusText);
        ok($('.error').text().indexOf(responseText) >= 0, responseText);
        equal(e.status, status);
    }

    $.ajax = ajax;
});

test("lookup_result", function() {
    expect(7);

    var caught = false;
    var what = 'WHAT';
    var error_regexp = /ERR_(.*)_OR/;
    var value = 'VALUE';
    var success_regexp = /SUC_(.*)_ESS/;

    // error
    try {
        $.bug.lookup_result('ERR_' + what + '_OR', [error_regexp], success_regexp);
    } catch(e) {
        equal(e[1], what);
        equal($('.error').text(), what);
        caught = true;
    }
    ok(caught, 'caught exception');

    // output is not as expected
    var bugous = 'BUGOUS OUTPUT';
    try {
        $.bug.lookup_result(bugous, [error_regexp], success_regexp);
    } catch(ee) {
        equal(ee, bugous);
        ok($('.error').text().indexOf(success_regexp) >= 0, 'error displayed');
        caught = true;
    }
    ok(caught, 'caught exception');

    // success
    equal($.bug.lookup_result('SUC_' + value + '_ESS', [error_regexp], success_regexp), value);
});

test("state_signin", function() {
    expect(11);

    equal($('.signin').css('display'), 'none');
    var user = 'gooduser';
    var password = 'goodpassword';
    $.bug.ajax = function(type, url, data, callback) {
        var d = $.Deferred();
        if(data.Bugzilla_login == user &&
           data.Bugzilla_password == password) {
            d.resolve('Log&nbsp;out</a>' + data.Bugzilla_login + '<');
        } else {
            d.resolve('class="throw_error">ERROR<');
        }
        return d;
    };
    var state_component = $.bug.state_component;
    $.bug.state_component = function() { ok(true, 'state_component'); };
    $.bug.state_signin();
    equal($('.login-link').attr('href'), '/');
    equal($('.create-account-link').attr('href'), '/createaccount.cgi');
    equal($('.signin').css('display'), 'block');
    // fail to login, shows error
    equal($('.error-container').css('display'), 'none', 'no error');
    try {
        $('.signin .go').click();
    } catch(e) {
        ok(true, 'caught error');
    }
    equal($('.error-container').css('display'), 'block', 'no error');
    // successfull login
    $('.signin .user').val(user);
    $('.signin .password').val(password);
    $('.signin .go').click();
    equal($('.signin').css('display'), 'none');
    equal($('.error-container').css('display'), 'none', 'no error');
    equal($('.username').text(), user);

    $.bug.ajax = $.ajax;
    $.bug.state_component = state_component;
});

test("state_component", function() {
    expect(15);

    var state_details = $.bug.state_details;
    $.bug.state_details = function() { ok(true, 'state_details'); };

    var element = $('.state_component');
    equal(element.css('display'), 'none');
    $.bug.state_component();
    equal(element.css('display'), 'block');
    equal($('.component .chosen', element).attr('data'), undefined, 'initialy nothing selected');
    equal($('.comment.Formula_editor', element).css('display'), 'none', 'Formula_editor hidden');
    equal($('.comment.OTHER', element).css('display'), 'none', 'OTHER hidden');
    equal($('img.selected').length, 0, 'no icon selected');
    // chosing Formula editor updates the comment, selects the icon and moves to subcomponent state
    $(".component .choice[data='Formula_editor']", element).click();
    equal($('img[data="Formula_editor"].selected', element).length, 1, 'Formula editor icon selected');
    equal($('.comment.Formula_editor', element).css('display'), 'block', 'Formula_editor is visible');
    equal($('.comment.OTHER', element).css('display'), 'none', 'OTHER hidden');
    // hovering on an icon changes the comment but has no effect on the selection
    $('img[data="OTHER"]', element).mouseenter();
    equal($('.comment.Formula_editor', element).css('display'), 'none', 'Formula_editor hidden');
    equal($('.comment.OTHER', element).css('display'), 'block', 'OTHER is visible');
    equal($('.component .chosen', element).attr('data'), 'Formula_editor');
    // leaving the icon area reverts back the comment to the selected element
    $('.components_icons', element).mouseleave();
    equal($('.comment.Formula_editor', element).css('display'), 'block', 'Formula_editor is visible');
    equal($('.comment.OTHER', element).css('display'), 'none', 'OTHER hidden');

    $.bug.state_details = state_details;
});

test("state_details", function() {
    expect(8);

    var state_version = $.bug.state_version;
    $.bug.state_version = function() { ok(true, 'state_version'); };
    var refresh_related_bugs = $.bug.refresh_related_bugs;
    $.bug.refresh_related_bugs = function() { ok(true, 'refresh_related_bugs'); };

    var element = $('.state_details');
    var element_sub = $('.subcomponents');
    var element_ver = $('.versions');
    var element_sys = $('.op_sys');
    equal(element.css('display'), 'none');
    ok(!element.hasClass('initialized'), 'is not initialized');
    equal($('.active_subcomponent .select', element).length, 0, 'no .select element');
    equal($('.versions .select', element).length, 0, 'no .select element');
    $(".state_component .chosen").attr('data', 'Formula_editor');
    /*var version = 'VERSION1';
    $(".versions .choice[data='" + version + "']", element).click();
    var op_sys = "LINUX"; 
    $(".op_sys .choice[data='" + op_sys + "']", element).click();*/
    $.bug.state_details();
    equal($('.active_subcomponent .select', element).length, 1, 'one .select element');
    equal($('.versions .chosen', element_ver).attr('data'), undefined, 'initialy nothing selected');
    equal(element.css('display'), 'block');
    $(".active_subcomponent .subcomponent .choice[data='Formula_editor']", element_sub).click();
    ok(true, 'state_details');
    $('.state_details .versions .choice:nth(0)').click();

    $.bug.state_version = state_version;
    $.bug.refresh_related_bugs = refresh_related_bugs;
});

test("state_description", function() {
    expect(5);

    var state_submit = $.bug.state_submit;
    $.bug.state_submit = function() { ok(true, 'state_submit'); };

    var element = $('.state_description');
    equal(element.css('display'), 'none');
    ok(!element.hasClass('initialized'), 'is not initialized');
    $.bug.state_description();
    equal(element.css('display'), 'block');
    ok(element.hasClass('initialized'), 'is initialized');
    $('.short', element).val('012345').change();
    $('.long', element).val('012345678901');
    $('.long', element).keyup();

    $.bug.state_submit = state_submit;
});

test("state_submit", function() {
    expect(30);

    var state_success = $.bug.state_success;
    $.bug.state_success = function() { ok(true, 'state_success'); };

    var element = $('.state_submit');
    $.bug.token = 'AA';
    equal(element.css('display'), 'none');
    ok(!element.hasClass('initialized'), 'is not initialized');
    $.bug.state_submit();
    equal(element.css('display'), 'block');
    ok(element.hasClass('initialized'), 'is initialized');
    $.bug.state_component();
    var component = 'Formula_editor';
    $(".state_component .choice[data='" + component + "']").click();
    var component_text = $(".state_component .chosen").text();
    $.bug.state_details();
    var subcomponent = 'SUBCOMPONENT';
    $.bug.subcomponent = subcomponent;
    var version = 'VERSION';
    $.bug.version = version;
    var op_sys = "LINUX";
    $.bug.op_sys = op_sys;
    var short_desc = 'SHORT_DESC';
    $('.state_description .short').val(short_desc);
    var comment = 'LONG';
    $('.state_description .long').val(comment);

    var bug = '40763';
    var form = $('.submission_form form');

    form.submit(function() {
        ok(element.hasClass('inprogress'), 'is in progress');
        ok(form.attr('action'), '/post_bug.cgi');
        equal($('input[name="component"]', form).val(), component_text);
        equal($('input[name="version"]', form).val(), version);
        equal($('input[name="short_desc"]', form).val(), subcomponent + ': ' + short_desc);
        equal($('input[name="comment"]', form).val(), comment + "\nOperating System: ");
        return false; // prevent actual submission
    });
    form.submit();
    form.submit(); // noop

    $.bug.state_submit_element = 'div'; // because <html> can't be inserted in the dom

    // <title> cannot be inserted by IE8
    $('#submissionoutput').html('<div><div>Bug ' + bug + ' Submitted</div></div>');
    $('#submissionoutput').load();
    equal($('.bug', element).text(), bug, 'bug number');
    ok(!element.hasClass('inprogress'), 'is no longer progress');

    var error = 'ERROR';
    equal($('.error').text(), '', 'error is not set');

    // make sure you enclose the useful elements with <div><div> ... </div></div>
    $(['<div><div><table cellpadding="20">   <tr>    <td bgcolor="#ff0000">      <font size="+2">' + error + '</font>   </td>  </tr> </table></div></div>',
       '<div><div><div class="throw_error">' + error + '</div></div></div>',
       '<div><div><div class="box">\n <p>' + error + '</p></div></div></div>'
      ]).each(function(index, str) {
        $('#submissionoutput').html(str);
        var caught = false;
        try {
            $('#submissionoutput').load();
        } catch(e) {
            equal($('.error').text(), error, 'text ' + str);
            equal(e[1], error, 'catch ' + str + e);
            caught = true;
        }
        ok(caught, 'caught', str);
    });
    equal($('.error').text(), error, 'error is set');

    $('.state_description').hide();
    $('.state_attach').hide();
    $('.state_submit').hide();
    $.bug.state_success = state_success;
    $.bug.ajax = $.ajax;
});

test("state_success", function() {
    expect(4);

    var bug = '4242';
    var element = $('.state_success');
    equal(element.css('display'), 'none');
    equal($('.submission').css('display'), 'block');
    $('.state_submit .bug').text(bug);
    $.bug.state_success();
    equal(element.css('display'), 'block');
    ok($('.bug', element).attr('href').indexOf(bug) > 0, 'bug found');
});

test("state_attach", function() {
    expect(4);

    var element = $('.state_attach');
    equal(element.css('display'), 'none');
    $.bug.state_attach();
    equal(element.css('display'), 'block');

    var container = $('.attach-file', element);
    var container_offset = container.offset();
    var file_input = $("input[type='file']", element);
    var file_input_width = file_input.outerWidth();


    equal(file_input.css('left'), 'auto');

    //
    // place the mouse to the left of the container
    // at a position where it is certain that the input type='file'
    // width will not fit.
    //
    var event = jQuery.Event("mousemove");
    event.pageX = container_offset.left + file_input_width / 2;
    event.pageY = container_offset.top;
    container.trigger(event);
    //
    // The input type='file' left position is to the left of the container,
    // hence a negative number starting with a -
    // This is proof that the input type='file' has been moved so that its
    // rightmost part is under the mouse at all times.
    //
    equal(file_input.css('left').substr(0, 1), '-', 'left = ' + file_input.css('left'));
});

test("logged_in", function() {
    expect(2);

    $.bug.ajax = function(type, url) {
        return $.Deferred().resolve($.bug.logged_in_false);
    };
    $.bug.logged_in().done(function(status) {
        equal(status, false, 'user not logged in');
    });

    $.bug.ajax = function(type, url) {
        return $.Deferred().resolve('logged in ok');
    };
    $.bug.logged_in().done(function(status) {
        equal(status, true, 'user is logged in');
    });

    $.bug.ajax = $.ajax;
});
