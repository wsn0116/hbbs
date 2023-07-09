#!/usr/local/bin/perl

# �d�l
#
#	$nameofthisfile (755)	���̃t�@�C��
#	$numfile (666)		    ���b�Z�[�W�i���o�[�t�@�C��
#	$rejectfile (666)		���e���ۃ��X�g�t�@�C���i���e���ۋ@�\�𗘗p����ꍇ�̂݁j

#--------------------------------------------------------------------------------------------------------------------#
# ���ʐݒ�
#--------------------------------------------------------------------------------------------------------------------#

# jcode.pl �̎w��
require "../jcode.pl";

require "../rejectlib.pl";

# ���̃t�@�C��
$nameofthisfile = "./hbbs.cgi";

# �x�[�X�ƂȂ� html �t�@�C��
$basefile = "./hbbs.dat";

# ���b�Z�[�W�i���o�[�t�@�C��
$numfile = "./hbbsmsgnum.dat";

# ��x�ɏ������߂�ʁi�P�ʁF�o�C�g�j
$comment_max_size = 10000;

# ���b�Z�[�W�i���o�[�̊J�n�ԍ�
$startmsgnumber = 1000;

# �e�L���̍ő�\������
$lines = 15;

# �ԐM�L���̍ő�\������
$replylines = 50;

#--------------------------------------------------------------------------------------------------------------------#
# �ݒ�
#--------------------------------------------------------------------------------------------------------------------#

# �g�b�v�y�[�W
$toppageaddress = "../../index.cgi";

# �g�p����J�X�P�[�h�X�^�C���V�[�g�t�@�C��
$cssfile = "../css.css";

#--------------------------------------------------------------------------------------------------------------------#
# ���C�����[�`��
#--------------------------------------------------------------------------------------------------------------------#

# POST �`���ŕW�����͂���ǂݍ���
 if ($ENV{'REQUEST_METHOD'} eq "POST") {
     read(STDIN, $Data, $ENV{'CONTENT_LENGTH'});
 } else {
     $Data = $ENV{'QUERY_STRING'};
 }
# �ǂݍ��݁E�������B

# �t�H�[���f�[�^�̃f�R�[�h����
 @pairs = split(/&/,$Data);
 foreach $pair (@pairs) {
     ($name,$value) = split(/=/, $pair);
     $value =~ tr/+/ /;
     $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

    # SJIS �ɃR�[�h�ϊ�
    &jcode'convert(*value, 'sjis');

    # �^�O�͖����i�^�O���̂�\������悤�ɒu���j
    $value =~ s/</&lt;/g;
    $value =~ s/>/&gt;/g;
    $value =~ s/\"/&quot;/g;

    if ($name eq "comment") {
        # �R�����g�t�H�[���̉��s�R�[�h�� <BR> �ɒu��
        $value =~ s/\r\n/<BR>/g;
        $value =~ s/\r/<BR>/g;
        $value =~ s/\n/<BR>/g;
    } else {
        # ���̃t�H�[���̉��s�R�[�h�͋󔒂ɒu��
        $value =~ s/\r//g;
        $value =~ s/\n//g;
    }

    # $FORM{'�t�H�[���� name'} �ɑ��
    $FORM{$name} = $value;
 }
# �f�R�[�h���������܂ŁB

# URL ���� http:// �����Ȃ�������A����� null ��
$url = $FORM{'url'};
if ($url eq "http://"){
    $url = "";
}

# �V�K���e���M�œn���ꂽ�� registnew �֐����Ăяo���B
if ( $FORM{'mode'} eq 'registnew' ) {
     if ($ENV{'REQUEST_METHOD'} eq "POST") {
        &registnew;
    }
}
# �t�H���[���e�t�H�[���\�� (printreplyform) �œn���ꂽ�� printreplyform �֐����Ăяo���B
if ( $FORM{'mode'} eq 'printreplyform' ) {
    &printscreen(0, "reply");
}
# �t�H���[���e���M�œn���ꂽ�� registreply �֐����Ăяo���B
if ( $FORM{'mode'} eq 'registreply' ) {
     if ($ENV{'REQUEST_METHOD'} eq "POST") {
        &registreply;
    }
}
# mode �ɉ��ɂ��n����ĂȂ������� printscreen �֐��ցB
&printscreen($startmsgnumber, "new");

# �����܂�
exit;

#--------------------------------------------------------------------------------------------------------------------#
# �T�u���[�`��
#--------------------------------------------------------------------------------------------------------------------#

# �ʏ��ʕ\���֐�
# 	��P����(@_[0])�F�\���J�n���b�Z�[�W�i���o�[
# 	��Q����(@_[1])�F new : �V�K���e�t�H�[��, reply : �t�H���[���e�t�H�[��
sub printscreen {

    my $source, $msg, $registform, $contribution, $contribution2;

    # ���i���΍�
    if ( $ENV{'HTTP_REFERER'} =~ /-_-/ ) {
        &error("�s���ȃv���L�V�����o���ꂽ�̂ŁA�A�N�Z�X�͋��ۂ���܂����B");
        exit;
    }

    # �x�[�X�t�@�C����ǂݍ���
    my $instance = &getdata($basefile);
    my @FILE = @$instance;

    # �z���A��
    my $source;
    foreach(@FILE) {
        $source .= $_;
    }

    # �V�K���e�̏ꍇ
    if (@_[1] eq "new") {
        # �V�K���e�t�H�[����\��
        $registform = &printnewform;

        # ���b�Z�[�W�i���o�[�̓ǂݍ��݁B
        if (!open(FILE,"$numfile")) {
            &error("file", "$numfile");
        }
        flock(FILE, 5);
        $number = <FILE>;
        close(FILE);
        flock(FILE, 8);

        # �L����\��
        $numend = $number - $lines;
        for($i=$number; $i>=$numend; $i--){
            # �t�@�C���`�F�b�N
            if (!open(FILE, "$i")){
                # �t�@�C�����Ȃ������烋�[�v����蒼��
                next;
            } else {
                close(FILE);
            }
            $contribution2 = &printscreen2($i, @_[1]);
            $contribution = "$contribution$contribution2";
        }
    }

    # �t�H���[���e�̏ꍇ
    if ( @_[1] eq "reply" ) {
        $registform = &printreplyform;

        # �t�H���[�ΏۋL����\��
         $contribution = "$contribution<DIV align=\"center\">\n<TABLE>\n";
         $contribution = "$contribution<TR><TH>�t�@�H�@���@�[�@�΁@�ہ@���@�e</TH></TR>\n";
        $contribution2 = &printscreen2($FORM{'follownumber'});
        $contribution = "$contribution$contribution2";
        $contribution = "$contribution</TD></TR>\n";
        $contribution = "$contribution</TABLE>\n</DIV>\n<BR>\n";
    }

    $msg = "$registform$contribution";

    $source =~ s/<\!--msg\/\/-->/$msg/g;

    # �x�[�X�t�@�C���̓��e��\��
     print "Content-type: text/html\n\n";
    print $source;

    # �����܂�
    exit;

}

sub printscreen2 {

    my $returnmsg = "";

    $numberps2 = @_[0];
    # ���b�Z�[�W�i���o�[�ɐ��l�ȊO���w�肳�ꂽ�ꍇ�́A�󔒂ɒu��
    $numberps2 =~ s/[^ 0-9]//g;
    # ���b�Z�[�W�i���o�[���󔒂�������I��
    if (!$numberps2) {
        exit;
    }

    if (!open(FILE, "@_[0]")){
        &error("file", "@_[0]", @_[0]);
        exit;
    }
    flock(FILE, 5);
    @FILE = <FILE>;
    close(FILE);
    flock(FILE, 8);

    # �܂��e�L����\��
    ($supernumber, $supersubject, $name, $mail, $remotehostcheck, $remotehost, $date, $comment, $url, $msgnum) = split(/&&/, shift(@FILE));
    # ���[���A�h���X�����͂���Ă��烊���N��\�����Ⴄ
    if ($mail){
        $name = "<A href=\"mailto:$mail\">$name</A>";
    }

    # ���`���ĕ\���i�e�L���j
    if (@_[1]) {
        $returnmsg = "$returnmsg<DIV align=center>\n";
        $returnmsg = "$returnmsg<TABLE>\n";
    }
    $returnmsg = "$returnmsg<TR><TD width=650 style=\"background-color: #A9ADED;\">";
    $returnmsg = "$returnmsg<B>No.</B>$supernumber�@<B><FONT size=-1>�薼�F</FONT> $supersubject</B><BR>\n";
    $returnmsg = "$returnmsg<FONT size=-1><B>���e�Җ��F</B> $name ";

    if ($remotehostcheck eq "check"){
        if ($remotehost) {
            $returnmsg = "$returnmsg\[$remotehost\]";
        } else {
            $returnmsg = "$returnmsg\[�����[�g�z�X�g���s��\]";
        }
    } else {
        $returnmsg = "$returnmsg\[�����[�g�z�X�g������J\]";
    }

    $returnmsg = "$returnmsg�@<B>���e���F</B>$date</FONT><BR>\n";
    $returnmsg = "$returnmsg</TD></TR><TR><TD width=650 style=\"padding: 10px 20px 0px 20px; background-color: #FFFFFF;\">";
    $comment =~ s/<BR>$//g;
    $returnmsg = "$returnmsg<BR>\n$comment\n<BR><BR>";

    # URL �����͂���Ă���AWebpage �����\��
    $url =~ s/\r//g;
    $url =~ s/\n//g;
    if ($url){
        $returnmsg = "$returnmsg<FONT size=-1><B>Webpage :</B></FONT>";
        $returnmsg = "$returnmsg <A href=\"$url\" target=\"_top\">$url</A><BR>\n";
    }

    # ���������A�ԐM���������ꍇ�ɂ͕ԐM��\��
    foreach $replylines (@FILE) {
        # ���o�`�B
        ($number, $subject, $name, $mail, $remotehostcheck, $remotehost, $date, $comment, $url, $msgnum) = split(/&&/, $replylines);

        # ���[���A�h���X�����͂���Ă��烊���N��\�����Ⴄ
        if ($mail){
            $name = "<A href=\"mailto:$mail\">$name</A>";
        }

        # ���`���ĕ\���i�ԐM�L���j
        $returnmsg = "$returnmsg<DIV class=\"indent\">\n<BR><HR>\n";
        $returnmsg = "$returnmsg<B>$number</B>�@<B><FONT size=-1>�薼�F</FONT> $subject</B><BR>\n";
        $returnmsg = "$returnmsg<FONT size=-1><B>���e�Җ��F</B> $name ";
            if ($remotehostcheck eq "check"){
                if ($remotehost) {
                    $returnmsg = "$returnmsg\[$remotehost\]";
                } else {
                    $returnmsg = "$returnmsg\[�����[�g�z�X�g���s��\]";
                }
            } else {
                $returnmsg = "$returnmsg\[�����[�g�z�X�g������J\]";
            }
        $comment =~ s/<BR>$//g;
        $returnmsg = "$returnmsg�@<B>���e���F</B>$date</FONT>\n<BR><BR>\n$comment<BR><BR>\n";

        # URL �����͂���Ă���AWebpage �����\��
        $url =~ s/\r//g;
        $url =~ s/\n//g;
        if ($url){
            $returnmsg = "$returnmsg<FONT size=-1><B>Webpage :</B></FONT>";
            $returnmsg = "$returnmsg <A href=\"$url\" target=\"_top\">$url</A><BR>\n";
        }
        $returnmsg = "$returnmsg</DIV>";
    }

    if (@_[1]) {
        $returnmsg = "$returnmsg<DIV align=right><FORM>\n";
        $returnmsg = "$returnmsg<INPUT type=\"hidden\" name=\"mode\" value=\"printreplyform\">\n";
        $returnmsg = "$returnmsg<INPUT type=\"hidden\" name=\"follownumber\" value=\"$supernumber\">\n";
        $returnmsg = "$returnmsg<INPUT type=\"hidden\" name=\"followsubject\" value=\"$supersubject\">\n";
        $returnmsg = "$returnmsg<INPUT type=\"submit\" value=\"���̏������݂̃t�H���[������\">\n";
        $returnmsg = "$returnmsg</FORM></DIV>\n</TD></TR></TABLE>\n</DIV>\n<BR><BR>\n";
    }

    return $returnmsg;
}

# �������ޏ���������֐�
sub registinit {
    # �󗓃`�F�b�N
    if ($FORM{'name'} eq "") { &error("���e�Җ���������ĂȂ��ł��B"); }
    if ($FORM{'subject'} eq "") { &error("�薼��������ĂȂ��ł��B"); }
    if ($FORM{'comment'} eq "") { &error("���e���Ȃ��悤�B"); }

    # �T�C�Y�`�F�b�N
    $comment_size = length($FORM{'comment'});
    if ($comment_size > $comment_max_size) {
        &error("$max_size �o�C�g�ȓ��ł��肢���܂��ł��B<BR>���Ȃ݂ɏ��������[�Ƃ����T�C�Y�� $value_size �o�C�g�ł��B");
    }

    # �ۑ��̂��߂̉��������̂P�F�����[�g�z�X�g���擾
    if($ENV{'REMOTE_HOST'} eq $ENV{'REMOTE_ADDR'}) {
        $remotehost = gethostbyaddr( pack( 'C4', split( /\./, $ENV{'REMOTE_ADDR'} ) ), 2 );
    } else {
        $remotehost = $ENV{'REMOTE_HOST'};
        if ($remotehost eq "") {
            $remotehost = $ENV{'REMOTE_ADDR'};
        }
    }

    # �ۑ��̂��߂̉��������̂Q�F�����̓��t�⌻�ݎ������擾
    $ENV{'TZ'} = "JST-9";
    $times = time;
    ($sec,$min,$hour,$mday,$mon,$year,$wday) = localtime($times);
    @weekdays = ('��','��','��','��','��','��','�y');
    $date = sprintf("%04d�N%02d��%02d��%s�j�� %02d��%02d��%02d�b", $year+1900, $mon+1, $mday, $weekdays[$wday], $hour, $min, $sec);

    # ���e���ۃ`�F�b�N
    my $result = &rejectcheck($remotehost, $FORM{'comment'}, $date);
    if ( $result eq 1 ) {
        &error("���e�����ۂ���܂����B");
    }
    if ( $result eq -1 ) {
        &error("���e���ɃG���[���������܂����B");
    }

}

# �V�K���e�ŏ������ނƂ��ɌĂяo�����֐�
sub registnew {
    # ����
    &registinit;

    # ���b�Z�[�W�i���o�[�̓ǂݍ���
    if (!open(FILE,"$numfile")) {
        &error("file", "$numfile");
    }
    flock(FILE, 5);
    $number = <FILE>;
    # ���b�Z�[�W�i���o�[�ɐ��l�ȊO���w�肳�ꂽ�ꍇ�́A�󔒂ɒu��
    $number =~ s/[^ 0-9]//g;
    close(FILE);
    flock(FILE, 8);
    # ���b�Z�[�W�i���o�[���󔒂�������I��
    if ($number eq "") {
        &footer;
        exit;
    }

    # ���b�Z�[�W�i���o�[���C���N�������g
    $number++;

    # �V�K���e�p�t�@�C���̐���
    system ("touch $number");
    if (!open(FILE,">$number")){
        &error("file", "$number");
    }

    $url =~ s/http:\/\/http:\/\//http:\/\//g;

    # �ۑ��f�[�^��z��ϐ��ɉ�������
    push(@savedata, "$number&&$FORM{'subject'}&&$FORM{'name'}&&$FORM{'mail'}&&$FORM{'remotehost'}&&$remotehost&&$date&&$FORM{'comment'}&&$url\n");

    # �L���f�[�^��ۑ�
    if (!open(FILE,">>$number")) {
        &error("file", "$number");
    }
    flock(FILE, 2);
    print FILE @savedata;
    close(FILE);
    flock(FILE, 8);

    # ���b�Z�[�W�i���o�[���ۑ�
    if (!open(FILE,">$numfile")) {
        &error("file", "$numfile");
    }
    flock(FILE, 2);
    print FILE $number;
    close(FILE);
    flock(FILE, 8);

    # ����i�΁j
    &error("�������݂��肪�Ƃ��ł��`�B");
    exit;
}

# �t�H���[���e�ŏ������ނƂ��ɌĂяo�����֐�
sub registreply {
    # ����
    &registinit;

    # �ۑ��f�[�^��z��ϐ��ɉ�������
    push(@savedata, "�ԐM&&$FORM{'subject'}&&$FORM{'name'}&&$FORM{'mail'}&&$FORM{'remotehost'}&&$remotehost&&$date&&$FORM{'comment'}&&$url\n");

    # �t�H���[���b�Z�[�W�i���o�[�ɐ��l�ȊO���w�肳�ꂽ�ꍇ�́A�󔒂ɒu��
    $FORM{'follownumber'} =~ s/[^ 0-9]//g;
    # �t�H���[���b�Z�[�W�i���o�[���󔒂�������I��
    if ($FORM{'follownumber'} eq "") {
        &footer;
        exit;
    }

    # �L���f�[�^��ۑ�
    if (!open(FILE,">>$FORM{'follownumber'}")) {
        &error("file", "$FORM{'follownumber'}", $FORM{'follownumber'});
    }
    flock(FILE, 2);
    print FILE @savedata;
    close(FILE);
    flock(FILE, 8);

    # ����i�΁j
    &error("�������݂��肪�Ƃ��ł��`�B");
    exit;
}

# �f�[�^���t�@�C������ǂݍ��ފ֐�
#	������	�F�t�@�C����
#	�ԋp�l		�F�ǂݏo�����f�[�^
sub getdata {
    my @FILE;

    if (!open(FILE, "@_")) {
        &error("file", "@_");
    }
    @FILE = <FILE>;
    close (FILE);

    return \@FILE;
}

# �G���[��ʕ\���֐�
#	��P�����F�G���[���b�Z�[�W�A�܂��� "file"�B
#	��Q�����F��P������ file ���w�肵���ꍇ�ɁA�t�@�C�������w��B
sub error {
    if ( @_[0] eq "file" ){
        $errmsg = "�t�@�C�� @_[1] ���J���Ȃ��̂ł����B";
    } else {
        $errmsg = @_[0];
    }

    &errheader;
    print "<BR><BR><H2>$errmsg</H2><BR><BR>\n";
    print "<DIV align=\"right\"><A href=\"$myself\">[�����[�h]</A> | <A href=\"$toppageaddress\">[�g�b�v�y�[�W�ɖ߂�]</A>\n";
    &footer;
    exit;
}

# ���쌠�\���֐�
sub copyright {
    print "<H5 align=\"right\">Handmade BBS - Copyright 2001-2006 by wsn0116.</H5>\n";
    print "<DIV align=\"right\">$ENV{'REMOTE_HOST'} - $ENV{'REMOTE_ADDR'}</DIV>\n";
}

#--------------------------------------------------------------------------------------------------------------------#
# �e��ʕ\���֐��Q�i�L���\�����͏����j
#--------------------------------------------------------------------------------------------------------------------#

# �G���[���b�Z�[�W�\�����A�܂��͓��e���肪�Ƃ���ʂ̂Ƃ��̃w�b�_
sub errheader {
     print "Content-type: text/html\n\n";
     print "<HTML>\n";
     print "<HEAD>\n";
     print "<META HTTP-EQUIV=\"Content-type\" CONTENT=\"text/html; charset=Shift_JIS\">\n";
     print "<TITLE>�f����</TITLE>\n";
     print "<LINK REL=\"stylesheet\" TYPE=\"text/css\" HREF=\"$cssfile\" MEDIA=\"all\">\n";
     print "</HEAD>\n";
     print "<BODY>\n";
    print "<DIV class=\"indent\">\n";
}

# �V�K���e�t�H�[����\������̂ɌĂяo�����֐�
sub printnewform {
    my $returnmsg;

     $returnmsg = "<DIV align=\"center\">\n";
     $returnmsg = "$returnmsg<FORM action=\"$nameofthisfile\" method=\"POST\">\n";
     $returnmsg = "$returnmsg<TABLE class=\"top-default\">\n";
     $returnmsg = "$returnmsg<TR><TH colspan=2>�V�@�K�@���@�e�@�t�@�H�@�[�@��</TH></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>���e��</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"name\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>���[��</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"mail\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>��@��</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"subject\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH rowspan=2>���@�e</TH>\n";
     $returnmsg = "$returnmsg<TD><INPUT type=\"checkbox\" name=\"remotehost\" value=\"check\" checked>�@<FONT size=-1>�����[�g�z�X�g����\�\\��\����</FONT></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TD><TEXTAREA wrap=\"soft\" name=\"comment\" rows=\"8\" cols=\"60\"></TEXTAREA></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>�t�q�k</TH><TD><INPUT type=\"text\" size=\"60\" name=\"url\" value=\"http://\"></TD></TR>\n";
     $returnmsg = "$returnmsg</TD></TR>\n";
     $returnmsg = "$returnmsg</TABLE>\n";
     $returnmsg = "$returnmsg<BR>\n";
     $returnmsg = "$returnmsg<INPUT type=\"hidden\" name=\"mode\" value=\"registnew\">\n";
     $returnmsg = "$returnmsg<INPUT type=\"submit\" value=\"�@�@�@�@�@�������݁@�@�@�@�@\"><INPUT type=\"reset\" value=\"�@�@�@�@�@�N���A�@�@�@�@�@\">\n";
     $returnmsg = "$returnmsg</FORM>\n";
     $returnmsg = "$returnmsg</DIV>\n";
     $returnmsg = "$returnmsg<BR>\n";
    $returnmsg = "$returnmsg<DIV align=\"right\"><A href=\"$nameofthisfile\">[�����[�h]</A> | <A href=\"$toppageaddress\">[�g�b�v�y�[�W�ɖ߂�]</A></DIV><BR><BR>";

    return $returnmsg;
}

# �t�H���[���e�t�H�[����\������̂ɌĂяo�����֐�
sub printreplyform {
    my $returnmsg;

    # �t�H���[���e�t�H�[����\��
     $returnmsg = "<DIV align=\"center\">\n";
     $returnmsg = "$returnmsg<FORM action=\"$nameofthisfile\" method=\"POST\">\n";
     $returnmsg = "$returnmsg<TABLE class=\"top-default\">\n";
     $returnmsg = "$returnmsg<TR><TH colspan=2>�t�@�H�@���@�[�@���@�e�@�t�@�H�@�[�@��</TH></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>���e��</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"name\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>���[��</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"mail\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>��@��</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"subject\" value=\"Re: $FORM{'followsubject'}\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH rowspan=2>���@�e</TH>\n";
     $returnmsg = "$returnmsg<TD><INPUT type=\"checkbox\" name=\"remotehost\" value=\"check\" checked>�@<FONT size=-1>�����[�g�z�X�g����\�\\��\����</FONT></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TD><TEXTAREA wrap=\"soft\" name=\"comment\" rows=\"8\" cols=\"60\"></TEXTAREA></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>�t�q�k</TH><TD><INPUT type=\"text\" size=\"60\" name=\"url\" value=\"http://\"></TD></TR>\n";
     $returnmsg = "$returnmsg</TD></TR>\n";
     $returnmsg = "$returnmsg</TABLE>\n";
      $returnmsg = "$returnmsg<BR>\n";
     $returnmsg = "$returnmsg<INPUT type=\"hidden\" name=\"mode\" value=\"registreply\">\n";
     $returnmsg = "$returnmsg<INPUT type=\"hidden\" name=\"follownumber\" value=\"$FORM{'follownumber'}\">\n";
     $returnmsg = "$returnmsg<INPUT type=\"submit\" value=\"�@�@�@�@�@�������݁@�@�@�@�@\"><INPUT type=\"reset\" value=\"�@�@�@�@�@�N���A�@�@�@�@�@\">\n";
     $returnmsg = "$returnmsg</FORM>\n";
     $returnmsg = "$returnmsg</DIV>\n";
     $returnmsg = "$returnmsg<BR>\n";
    $returnmsg = "$returnmsg<DIV align=\"right\"><A href=\"$nameofthisfile\">[�t�H���[���e����߂Ė߂�]</A> | <A href=\"$toppageaddress\">[�g�b�v�y�[�W�ɖ߂�]</A></DIV><BR><BR>\n";

    return $returnmsg;
}

# �t�b�^�i�ʏ펞�E�G���[�����p�j
sub footer {
    &copyright;
    print "</DIV>\n";
    print "</BODY>\n</HTML>\n";
}

#--------------------------------------------------------------------------------------------------------------------#
# �����܂� (- -)/~~
#--------------------------------------------------------------------------------------------------------------------#
