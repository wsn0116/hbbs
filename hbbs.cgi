#!/usr/local/bin/perl

# 仕様
#
#	$nameofthisfile (755)	このファイル
#	$numfile (666)		    メッセージナンバーファイル
#	$rejectfile (666)		投稿拒否リストファイル（投稿拒否機能を利用する場合のみ）

#--------------------------------------------------------------------------------------------------------------------#
# 共通設定
#--------------------------------------------------------------------------------------------------------------------#

# jcode.pl の指定
require "../jcode.pl";

require "../rejectlib.pl";

# このファイル
$nameofthisfile = "./hbbs.cgi";

# ベースとなる html ファイル
$basefile = "./hbbs.dat";

# メッセージナンバーファイル
$numfile = "./hbbsmsgnum.dat";

# 一度に書き込める量（単位：バイト）
$comment_max_size = 10000;

# メッセージナンバーの開始番号
$startmsgnumber = 1000;

# 親記事の最大表示件数
$lines = 15;

# 返信記事の最大表示件数
$replylines = 50;

#--------------------------------------------------------------------------------------------------------------------#
# 設定
#--------------------------------------------------------------------------------------------------------------------#

# トップページ
$toppageaddress = "../../index.cgi";

# 使用するカスケードスタイルシートファイル
$cssfile = "../css.css";

#--------------------------------------------------------------------------------------------------------------------#
# メインルーチン
#--------------------------------------------------------------------------------------------------------------------#

# POST 形式で標準入力から読み込み
 if ($ENV{'REQUEST_METHOD'} eq "POST") {
     read(STDIN, $Data, $ENV{'CONTENT_LENGTH'});
 } else {
     $Data = $ENV{'QUERY_STRING'};
 }
# 読み込み・完了っ。

# フォームデータのデコード処理
 @pairs = split(/&/,$Data);
 foreach $pair (@pairs) {
     ($name,$value) = split(/=/, $pair);
     $value =~ tr/+/ /;
     $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

    # SJIS にコード変換
    &jcode'convert(*value, 'sjis');

    # タグは無効（タグ自体を表示するように置換）
    $value =~ s/</&lt;/g;
    $value =~ s/>/&gt;/g;
    $value =~ s/\"/&quot;/g;

    if ($name eq "comment") {
        # コメントフォームの改行コードを <BR> に置換
        $value =~ s/\r\n/<BR>/g;
        $value =~ s/\r/<BR>/g;
        $value =~ s/\n/<BR>/g;
    } else {
        # 他のフォームの改行コードは空白に置換
        $value =~ s/\r//g;
        $value =~ s/\n//g;
    }

    # $FORM{'フォームの name'} に代入
    $FORM{$name} = $value;
 }
# デコード処理ここまで。

# URL 欄に http:// しかなかったら、それは null に
$url = $FORM{'url'};
if ($url eq "http://"){
    $url = "";
}

# 新規投稿送信で渡されたら registnew 関数を呼び出す。
if ( $FORM{'mode'} eq 'registnew' ) {
     if ($ENV{'REQUEST_METHOD'} eq "POST") {
        &registnew;
    }
}
# フォロー投稿フォーム表示 (printreplyform) で渡されたら printreplyform 関数を呼び出す。
if ( $FORM{'mode'} eq 'printreplyform' ) {
    &printscreen(0, "reply");
}
# フォロー投稿送信で渡されたら registreply 関数を呼び出す。
if ( $FORM{'mode'} eq 'registreply' ) {
     if ($ENV{'REQUEST_METHOD'} eq "POST") {
        &registreply;
    }
}
# mode に何にも渡されてなかったら printscreen 関数へ。
&printscreen($startmsgnumber, "new");

# おしまい
exit;

#--------------------------------------------------------------------------------------------------------------------#
# サブルーチン
#--------------------------------------------------------------------------------------------------------------------#

# 通常画面表示関数
# 	第１引数(@_[0])：表示開始メッセージナンバー
# 	第２引数(@_[1])： new : 新規投稿フォーム, reply : フォロー投稿フォーム
sub printscreen {

    my $source, $msg, $registform, $contribution, $contribution2;

    # 多段串対策
    if ( $ENV{'HTTP_REFERER'} =~ /-_-/ ) {
        &error("不正なプロキシが検出されたので、アクセスは拒否されますた。");
        exit;
    }

    # ベースファイルを読み込み
    my $instance = &getdata($basefile);
    my @FILE = @$instance;

    # 配列を連結
    my $source;
    foreach(@FILE) {
        $source .= $_;
    }

    # 新規投稿の場合
    if (@_[1] eq "new") {
        # 新規投稿フォームを表示
        $registform = &printnewform;

        # メッセージナンバーの読み込み。
        if (!open(FILE,"$numfile")) {
            &error("file", "$numfile");
        }
        flock(FILE, 5);
        $number = <FILE>;
        close(FILE);
        flock(FILE, 8);

        # 記事を表示
        $numend = $number - $lines;
        for($i=$number; $i>=$numend; $i--){
            # ファイルチェック
            if (!open(FILE, "$i")){
                # ファイルがなかったらループをやり直し
                next;
            } else {
                close(FILE);
            }
            $contribution2 = &printscreen2($i, @_[1]);
            $contribution = "$contribution$contribution2";
        }
    }

    # フォロー投稿の場合
    if ( @_[1] eq "reply" ) {
        $registform = &printreplyform;

        # フォロー対象記事を表示
         $contribution = "$contribution<DIV align=\"center\">\n<TABLE>\n";
         $contribution = "$contribution<TR><TH>フ　ォ　ロ　ー　対　象　投　稿</TH></TR>\n";
        $contribution2 = &printscreen2($FORM{'follownumber'});
        $contribution = "$contribution$contribution2";
        $contribution = "$contribution</TD></TR>\n";
        $contribution = "$contribution</TABLE>\n</DIV>\n<BR>\n";
    }

    $msg = "$registform$contribution";

    $source =~ s/<\!--msg\/\/-->/$msg/g;

    # ベースファイルの内容を表示
     print "Content-type: text/html\n\n";
    print $source;

    # おしまい
    exit;

}

sub printscreen2 {

    my $returnmsg = "";

    $numberps2 = @_[0];
    # メッセージナンバーに数値以外が指定された場合は、空白に置換
    $numberps2 =~ s/[^ 0-9]//g;
    # メッセージナンバーが空白だったら終了
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

    # まず親記事を表示
    ($supernumber, $supersubject, $name, $mail, $remotehostcheck, $remotehost, $date, $comment, $url, $msgnum) = split(/&&/, shift(@FILE));
    # メールアドレスが入力されてたらリンクを貼っちゃう
    if ($mail){
        $name = "<A href=\"mailto:$mail\">$name</A>";
    }

    # 整形して表示（親記事）
    if (@_[1]) {
        $returnmsg = "$returnmsg<DIV align=center>\n";
        $returnmsg = "$returnmsg<TABLE>\n";
    }
    $returnmsg = "$returnmsg<TR><TD width=650 style=\"background-color: #A9ADED;\">";
    $returnmsg = "$returnmsg<B>No.</B>$supernumber　<B><FONT size=-1>題名：</FONT> $supersubject</B><BR>\n";
    $returnmsg = "$returnmsg<FONT size=-1><B>投稿者名：</B> $name ";

    if ($remotehostcheck eq "check"){
        if ($remotehost) {
            $returnmsg = "$returnmsg\[$remotehost\]";
        } else {
            $returnmsg = "$returnmsg\[リモートホスト名不明\]";
        }
    } else {
        $returnmsg = "$returnmsg\[リモートホスト名非公開\]";
    }

    $returnmsg = "$returnmsg　<B>投稿日：</B>$date</FONT><BR>\n";
    $returnmsg = "$returnmsg</TD></TR><TR><TD width=650 style=\"padding: 10px 20px 0px 20px; background-color: #FFFFFF;\">";
    $comment =~ s/<BR>$//g;
    $returnmsg = "$returnmsg<BR>\n$comment\n<BR><BR>";

    # URL が入力されてたら、Webpage 欄も表示
    $url =~ s/\r//g;
    $url =~ s/\n//g;
    if ($url){
        $returnmsg = "$returnmsg<FONT size=-1><B>Webpage :</B></FONT>";
        $returnmsg = "$returnmsg <A href=\"$url\" target=\"_top\">$url</A><BR>\n";
    }

    # 引き続き、返信があった場合には返信を表示
    foreach $replylines (@FILE) {
        # 抽出～。
        ($number, $subject, $name, $mail, $remotehostcheck, $remotehost, $date, $comment, $url, $msgnum) = split(/&&/, $replylines);

        # メールアドレスが入力されてたらリンクを貼っちゃう
        if ($mail){
            $name = "<A href=\"mailto:$mail\">$name</A>";
        }

        # 整形して表示（返信記事）
        $returnmsg = "$returnmsg<DIV class=\"indent\">\n<BR><HR>\n";
        $returnmsg = "$returnmsg<B>$number</B>　<B><FONT size=-1>題名：</FONT> $subject</B><BR>\n";
        $returnmsg = "$returnmsg<FONT size=-1><B>投稿者名：</B> $name ";
            if ($remotehostcheck eq "check"){
                if ($remotehost) {
                    $returnmsg = "$returnmsg\[$remotehost\]";
                } else {
                    $returnmsg = "$returnmsg\[リモートホスト名不明\]";
                }
            } else {
                $returnmsg = "$returnmsg\[リモートホスト名非公開\]";
            }
        $comment =~ s/<BR>$//g;
        $returnmsg = "$returnmsg　<B>投稿日：</B>$date</FONT>\n<BR><BR>\n$comment<BR><BR>\n";

        # URL が入力されてたら、Webpage 欄も表示
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
        $returnmsg = "$returnmsg<INPUT type=\"submit\" value=\"この書き込みのフォローを書く\">\n";
        $returnmsg = "$returnmsg</FORM></DIV>\n</TD></TR></TABLE>\n</DIV>\n<BR><BR>\n";
    }

    return $returnmsg;
}

# 書き込む準備をする関数
sub registinit {
    # 空欄チェック
    if ($FORM{'name'} eq "") { &error("投稿者名が書かれてないです。"); }
    if ($FORM{'subject'} eq "") { &error("題名が書かれてないです。"); }
    if ($FORM{'comment'} eq "") { &error("内容がないよう。"); }

    # サイズチェック
    $comment_size = length($FORM{'comment'});
    if ($comment_size > $comment_max_size) {
        &error("$max_size バイト以内でお願いしますです。<BR>ちなみに書き込もーとしたサイズは $value_size バイトです。");
    }

    # 保存のための下準備その１：リモートホスト名取得
    if($ENV{'REMOTE_HOST'} eq $ENV{'REMOTE_ADDR'}) {
        $remotehost = gethostbyaddr( pack( 'C4', split( /\./, $ENV{'REMOTE_ADDR'} ) ), 2 );
    } else {
        $remotehost = $ENV{'REMOTE_HOST'};
        if ($remotehost eq "") {
            $remotehost = $ENV{'REMOTE_ADDR'};
        }
    }

    # 保存のための下準備その２：今日の日付や現在時刻を取得
    $ENV{'TZ'} = "JST-9";
    $times = time;
    ($sec,$min,$hour,$mday,$mon,$year,$wday) = localtime($times);
    @weekdays = ('日','月','火','水','木','金','土');
    $date = sprintf("%04d年%02d月%02d日%s曜日 %02d時%02d分%02d秒", $year+1900, $mon+1, $mday, $weekdays[$wday], $hour, $min, $sec);

    # 投稿拒否チェック
    my $result = &rejectcheck($remotehost, $FORM{'comment'}, $date);
    if ( $result eq 1 ) {
        &error("投稿が拒否されますた。");
    }
    if ( $result eq -1 ) {
        &error("投稿時にエラーが発生しました。");
    }

}

# 新規投稿で書き込むときに呼び出される関数
sub registnew {
    # 準備
    &registinit;

    # メッセージナンバーの読み込み
    if (!open(FILE,"$numfile")) {
        &error("file", "$numfile");
    }
    flock(FILE, 5);
    $number = <FILE>;
    # メッセージナンバーに数値以外が指定された場合は、空白に置換
    $number =~ s/[^ 0-9]//g;
    close(FILE);
    flock(FILE, 8);
    # メッセージナンバーが空白だったら終了
    if ($number eq "") {
        &footer;
        exit;
    }

    # メッセージナンバーをインクリメント
    $number++;

    # 新規投稿用ファイルの生成
    system ("touch $number");
    if (!open(FILE,">$number")){
        &error("file", "$number");
    }

    $url =~ s/http:\/\/http:\/\//http:\/\//g;

    # 保存データを配列変数に押し込む
    push(@savedata, "$number&&$FORM{'subject'}&&$FORM{'name'}&&$FORM{'mail'}&&$FORM{'remotehost'}&&$remotehost&&$date&&$FORM{'comment'}&&$url\n");

    # 記事データを保存
    if (!open(FILE,">>$number")) {
        &error("file", "$number");
    }
    flock(FILE, 2);
    print FILE @savedata;
    close(FILE);
    flock(FILE, 8);

    # メッセージナンバーも保存
    if (!open(FILE,">$numfile")) {
        &error("file", "$numfile");
    }
    flock(FILE, 2);
    print FILE $number;
    close(FILE);
    flock(FILE, 8);

    # お礼（笑）
    &error("書き込みありがとうです～。");
    exit;
}

# フォロー投稿で書き込むときに呼び出される関数
sub registreply {
    # 準備
    &registinit;

    # 保存データを配列変数に押し込む
    push(@savedata, "返信&&$FORM{'subject'}&&$FORM{'name'}&&$FORM{'mail'}&&$FORM{'remotehost'}&&$remotehost&&$date&&$FORM{'comment'}&&$url\n");

    # フォローメッセージナンバーに数値以外が指定された場合は、空白に置換
    $FORM{'follownumber'} =~ s/[^ 0-9]//g;
    # フォローメッセージナンバーが空白だったら終了
    if ($FORM{'follownumber'} eq "") {
        &footer;
        exit;
    }

    # 記事データを保存
    if (!open(FILE,">>$FORM{'follownumber'}")) {
        &error("file", "$FORM{'follownumber'}", $FORM{'follownumber'});
    }
    flock(FILE, 2);
    print FILE @savedata;
    close(FILE);
    flock(FILE, 8);

    # お礼（笑）
    &error("書き込みありがとうです～。");
    exit;
}

# データをファイルから読み込む関数
#	第一引数	：ファイル名
#	返却値		：読み出したデータ
sub getdata {
    my @FILE;

    if (!open(FILE, "@_")) {
        &error("file", "@_");
    }
    @FILE = <FILE>;
    close (FILE);

    return \@FILE;
}

# エラー画面表示関数
#	第１引数：エラーメッセージ、または "file"。
#	第２引数：第１引数で file を指定した場合に、ファイル名を指定。
sub error {
    if ( @_[0] eq "file" ){
        $errmsg = "ファイル @_[1] が開けないのですぅ。";
    } else {
        $errmsg = @_[0];
    }

    &errheader;
    print "<BR><BR><H2>$errmsg</H2><BR><BR>\n";
    print "<DIV align=\"right\"><A href=\"$myself\">[リロード]</A> | <A href=\"$toppageaddress\">[トップページに戻る]</A>\n";
    &footer;
    exit;
}

# 著作権表示関数
sub copyright {
    print "<H5 align=\"right\">Handmade BBS - Copyright 2001-2006 by wsn0116.</H5>\n";
    print "<DIV align=\"right\">$ENV{'REMOTE_HOST'} - $ENV{'REMOTE_ADDR'}</DIV>\n";
}

#--------------------------------------------------------------------------------------------------------------------#
# 各画面表示関数群（記事表示部は除く）
#--------------------------------------------------------------------------------------------------------------------#

# エラーメッセージ表示時、または投稿ありがとう画面のときのヘッダ
sub errheader {
     print "Content-type: text/html\n\n";
     print "<HTML>\n";
     print "<HEAD>\n";
     print "<META HTTP-EQUIV=\"Content-type\" CONTENT=\"text/html; charset=Shift_JIS\">\n";
     print "<TITLE>掲示板</TITLE>\n";
     print "<LINK REL=\"stylesheet\" TYPE=\"text/css\" HREF=\"$cssfile\" MEDIA=\"all\">\n";
     print "</HEAD>\n";
     print "<BODY>\n";
    print "<DIV class=\"indent\">\n";
}

# 新規投稿フォームを表示するのに呼び出される関数
sub printnewform {
    my $returnmsg;

     $returnmsg = "<DIV align=\"center\">\n";
     $returnmsg = "$returnmsg<FORM action=\"$nameofthisfile\" method=\"POST\">\n";
     $returnmsg = "$returnmsg<TABLE class=\"top-default\">\n";
     $returnmsg = "$returnmsg<TR><TH colspan=2>新　規　投　稿　フ　ォ　ー　ム</TH></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>投稿者</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"name\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>メール</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"mail\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>題　名</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"subject\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH rowspan=2>内　容</TH>\n";
     $returnmsg = "$returnmsg<TD><INPUT type=\"checkbox\" name=\"remotehost\" value=\"check\" checked>　<FONT size=-1>リモートホスト名を\表\示\する</FONT></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TD><TEXTAREA wrap=\"soft\" name=\"comment\" rows=\"8\" cols=\"60\"></TEXTAREA></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>ＵＲＬ</TH><TD><INPUT type=\"text\" size=\"60\" name=\"url\" value=\"http://\"></TD></TR>\n";
     $returnmsg = "$returnmsg</TD></TR>\n";
     $returnmsg = "$returnmsg</TABLE>\n";
     $returnmsg = "$returnmsg<BR>\n";
     $returnmsg = "$returnmsg<INPUT type=\"hidden\" name=\"mode\" value=\"registnew\">\n";
     $returnmsg = "$returnmsg<INPUT type=\"submit\" value=\"　　　　　書き込み　　　　　\"><INPUT type=\"reset\" value=\"　　　　　クリア　　　　　\">\n";
     $returnmsg = "$returnmsg</FORM>\n";
     $returnmsg = "$returnmsg</DIV>\n";
     $returnmsg = "$returnmsg<BR>\n";
    $returnmsg = "$returnmsg<DIV align=\"right\"><A href=\"$nameofthisfile\">[リロード]</A> | <A href=\"$toppageaddress\">[トップページに戻る]</A></DIV><BR><BR>";

    return $returnmsg;
}

# フォロー投稿フォームを表示するのに呼び出される関数
sub printreplyform {
    my $returnmsg;

    # フォロー投稿フォームを表示
     $returnmsg = "<DIV align=\"center\">\n";
     $returnmsg = "$returnmsg<FORM action=\"$nameofthisfile\" method=\"POST\">\n";
     $returnmsg = "$returnmsg<TABLE class=\"top-default\">\n";
     $returnmsg = "$returnmsg<TR><TH colspan=2>フ　ォ　ロ　ー　投　稿　フ　ォ　ー　ム</TH></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>投稿者</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"name\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>メール</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"mail\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>題　名</TH><TD><INPUT type=\"text\" size=\"60\" maxlength=\"80\" name=\"subject\" value=\"Re: $FORM{'followsubject'}\"></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH rowspan=2>内　容</TH>\n";
     $returnmsg = "$returnmsg<TD><INPUT type=\"checkbox\" name=\"remotehost\" value=\"check\" checked>　<FONT size=-1>リモートホスト名を\表\示\する</FONT></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TD><TEXTAREA wrap=\"soft\" name=\"comment\" rows=\"8\" cols=\"60\"></TEXTAREA></TD></TR>\n";
     $returnmsg = "$returnmsg<TR><TH>ＵＲＬ</TH><TD><INPUT type=\"text\" size=\"60\" name=\"url\" value=\"http://\"></TD></TR>\n";
     $returnmsg = "$returnmsg</TD></TR>\n";
     $returnmsg = "$returnmsg</TABLE>\n";
      $returnmsg = "$returnmsg<BR>\n";
     $returnmsg = "$returnmsg<INPUT type=\"hidden\" name=\"mode\" value=\"registreply\">\n";
     $returnmsg = "$returnmsg<INPUT type=\"hidden\" name=\"follownumber\" value=\"$FORM{'follownumber'}\">\n";
     $returnmsg = "$returnmsg<INPUT type=\"submit\" value=\"　　　　　書き込み　　　　　\"><INPUT type=\"reset\" value=\"　　　　　クリア　　　　　\">\n";
     $returnmsg = "$returnmsg</FORM>\n";
     $returnmsg = "$returnmsg</DIV>\n";
     $returnmsg = "$returnmsg<BR>\n";
    $returnmsg = "$returnmsg<DIV align=\"right\"><A href=\"$nameofthisfile\">[フォロー投稿をやめて戻る]</A> | <A href=\"$toppageaddress\">[トップページに戻る]</A></DIV><BR><BR>\n";

    return $returnmsg;
}

# フッタ（通常時・エラー時共用）
sub footer {
    &copyright;
    print "</DIV>\n";
    print "</BODY>\n</HTML>\n";
}

#--------------------------------------------------------------------------------------------------------------------#
# おしまい (- -)/~~
#--------------------------------------------------------------------------------------------------------------------#
