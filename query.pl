
#
#     Copyright (C) 2011 Loic Dachary <loic@dachary.org>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http:www.gnu.org/licenses/>.
#

use Scalar::Util qw(looks_like_number);


# Create a blacklist of version #s that we don't want to appear in the
# BSA anymore.
open(FILE, "version-blacklist.txt") or die ("Unable to open version blacklist.");
%blacklist = map { chomp; $_ => 1 } ( <FILE> );
close(FILE);

# Function to get version #s from query.cgi (url below):
# https://bugs.freedesktop.org/query.cgi?product=LibreOffice&query_format=advanced
sub version_numbers_from_query_cgi {
    while(<STDIN>) {
	eval $_ if(s/(cpts|vers)\[(\d+)\]\s+=/\$$1\[$2\]=/);
	if(/<select\s+name="product"/../<\/select/) {
	    if(/libreoffice/i) {
		$libreoffice = $count;
	    }
	    if(/<select\s+name="product"/) {
		$count = 0;
	    } elsif(/<option/) {
		$count++;
	    }
	}
    }

    return @{$vers[$libreoffice]};
}

# Function to get version #s from enter_bug.cgi (url below):
# https://bugs.freedesktop.org/enter_bug.cgi?product=LibreOffice&bug_status=UNCONFIRMED
#
# The big reason to use enter_bug.cgi is that it will not include
# "inactive" version numbers that we do not want to present as an
# option to users when filing new bugs. For more info, see:
# https://bugs.freedesktop.org/show_bug.cgi?id=55460
sub version_numbers_from_enter_bug_cgi {
    $time_to_nom_versions = 0;
    @versions = ();

    while(<STDIN>) {
	if($time_to_nom_versions) {
	    # Read-in all of the versions stored as OPTION values.
	    if(m/.*<option value="(.*)">.*/) {
		push(@versions, $1);
	    } else {
		# We've reached the end of the list of versions and no
		# longer need to read from this file.
		last;
	    }
	} elsif(m/<select name="version"/) {
	    $time_to_nom_versions = 1;
	}
    }
    
    return @versions;
}

# We can handle processing version #s from either query.cgi or from
# enter_bug.cgi.
#@unsorted_versions = version_numbers_from_query_cgi();
@unsorted_versions = version_numbers_from_enter_bug_cgi();


@versions = sort { 
    if (looks_like_number(substr($a, 0, 1)) == 0) { 
        return 1;
    } elsif (looks_like_number(substr($b, 0, 1)) == 0) {
        return -1;
    } else {
        return lc($b) cmp lc($a);
    } } @unsorted_versions;

print "<?xml version='1.0' encoding='ISO-8859-1'?>\n";

print <<EOF;
            <div class="select-header">
              <div class="chosen">$ARGV[0]</div>
            </div>
            <div class="choices">
              <div class="select-top">
                <div class="select-left">
                  <div class="select-bottom">
                    <div class="select-right">
                      <div class="top-left"></div>
                      <div class="top-right"></div>
                      <div class="bottom-left"></div>
                      <div class="bottom-right"></div>
                      <div class="center">
                        <ul>
EOF
    print " <li class='choice' data='NONE' idvalue='-1'>$ARGV[1]</li>\n";
    for($count = 0; $count < @versions; $count++) {
        # Ignore blacklisted versions.
        unless ( $blacklist{$versions[$count]} ) {
            print " <li class='choice' data='$versions[$count]' idvalue='$count'>$versions[$count]</li>\n";
	}
    }
    print <<EOF;
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
EOF

