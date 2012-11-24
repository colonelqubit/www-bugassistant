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

(function($) {

  $.skin = function() {
      $('.skin').show();
      $.bug.frame();
      $.bug.compatibility();
      function component() {
          $.bug.state_component();
      }
      function subcomponent() {
          component();
          $('.state_component .choice:nth(0)').click();
      }
      function version() {
          subcomponent();
          $.bug.ajax = function(settings) {
              return $.Deferred().resolve('NUM,DESC\n100,"BUG 1"\n200,"BUG 2"\n');
          };
          $('.state_subcomponent .active_subcomponent .choice:nth(0)').click();
      }
      function op_sys(){
          version();
          $('.state_version .choice:nth(0)').click();
      }
      function description() {
          op_sys();
          $('.state_op_sys .choice:nth(0)').click();
          $('.state_description .short').val('12');
      }
      function submit() {
          description();
          $('.state_description .short').val('1234567890');
          $('.state_description .long').val('12345678901');
          $('.state_description .short').change();
      }

      if(location.search.indexOf('skin=login') >= 0) {
          $.bug.state_signin();
          $.bug.error_set("THIS IS AN ERROR MESSAGE");
      } else if(location.search.indexOf('skin=component') >= 0) {
          component();
      } else if(location.search.indexOf('skin=subcomponent') >= 0) {
          subcomponent();
      } else if(location.search.indexOf('skin=version') >= 0) {
          version();
      } else if(location.search.indexOf('skin=op_sys') >= 0) {
          op_sys();
      } else if(location.search.indexOf('skin=description') >= 0) {
          description();
      } else if(location.search.indexOf('skin=submit') >= 0) {
          submit();
      } else if(location.search.indexOf('skin=complete') >= 0) {
          $.bug.state_success();
      }
  };

})(jQuery);
