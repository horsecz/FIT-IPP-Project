<?php
/*
*   IPP projekt: cast 2 - test.php
*   Autor: Dominik Horky
*   VUT FIT, 2021
*/

# TODO:     HTML
#           testovani parse-only, testovani both

###
### MAIN
###

$HELP_MSG = "Napoveda k skriptu 'test.php'.
Skript slouzi pro automaticke testovani (postupne) aplikace 'parse.php' a 'interpret.py'. Po otestovani skript generuje (na stdout) souhrn v HTML5.
Spusteni: test.php [--help][--directory=path][--recursive][--parse-script=file][--int-script=file][--parse-only][--int-only][--jexamxml=file][--jexamcfg=file]

Parametry:
    --help                  vypise tuto zpravu a ukonci skript
    --directory=path        testy bude hledat v zadanem adresari
                            (chybi-li tento parametr, skript prochazi aktualni adresar)
    --recursive             testy bude hledat i rekurzivne ve vsech podadresarich
    --parse-script=file     soubor se skriptem v PHP 7.4 pro analyzu kodu v IPPcode21
                            (chybi-li tento parametr, implicitni hodnotou je 'parse.php' ulozeny v aktualnim adresari)
    --int-script=file       soubor se skriptem v Python 3.8 pro interpret XML reprezentace kodu v IPPcode21
                            (chybi-li tento parametr, implicitni hodnotou je 'interpret.py' ulozeny v aktualnim adresari)
    --parse-only            bude testovan pouze skript pro analyzu zdrojoveho kodu v IPPcode21
                            (parametr se nesmi kombinovat s parametry --int-only a --int-script)
    --int-only              bude testovat pouze skript pro interpret XML reprezentace kodu v IPPcode21
                            (parametr se nesmi kombinovat s parametry --parse-only a --parse-script)
    --jexamxml=file         soubor s JAR balickem s nastrojem A7Soft JExamXML
                            (je-li parametr vynechan, implicitni umisteni je '/pub/courses/ipp/jexamxml/jexamxml.jar')
    --jexamcfg=file         soubor s konfiguraci nastroje A7Soft JExamXML
                            (je-li parametr vynechan, implicitni umisteni je '/pub/courses/ipp/jexamxml/options')
    --verbose               vypisuje prubeh skriptu na STDERR
";
$RECURSIVE = false;
$INT_ONLY = false;
$PARSE_ONLY = false;
$PARSE_SCRIPT = "";
$INT_SCRIPT = "";
$DIRECTORY = "";
$JEXAMXML = "";
$JEXAMCFG = "";
$CWD = getcwd();

$TESTS_CNT = 0;
$TESTS_PASSED_CNT = 0;
$TESTS_FAILED_CNT = 0;
$TESTS_FAILED = array();
$TESTS_FILES = array();
$TESTS_INV = array();


parseArguments($argc, $argv);
checkInput();
test();
generateHTML();

###
### FUNKCE
###

/*
*  Ukonci testovaci skript s navratovym kodem a hlaskou.
*/
function test_exit($exitCode, $exitMessage) {
    switch($exitCode) {
        case 10:
            $exitReason = "parametry";
            break;
        case 11:
            $exitReason = "vstupni soubory";
            break;
        case 12:
            $exitReason = "vystupni soubory";
            break;
        case 41:
            $exitReason = "test";
            break;
        case 99:
            $exitReason = "interni";
            break;
        default:
            fprintf(STDERR, "INTERNI CHYBA SKRIPTU: Neznamy navratovy kod '%d'.\n", $exitCode);
            exit(100);
            break;
    }
    fprintf(STDERR, "CHYBA [%s]: %s\n", $exitReason, $exitMessage);
    exit($exitCode);
}

/*
*   Parsuje argumenty skriptu test.php
*/
function parseArguments($argc, $argv) {
    global $RECURSIVE;
    global $INT_ONLY;
    global $PARSE_ONLY;
    global $PARSE_SCRIPT;
    global $INT_SCRIPT;
    global $DIRECTORY;
    global $JEXAMXML;
    global $JEXAMCFG;
    global $CWD;
    global $VERBOSE;

    $j = 0;
    $arg_array = array();
    for ($i = 1; $i < $argc; $i++) {
        switch($argv[$i]) {
            case '--help':
                printf("%s",$HELP_MSG);
                exit(0);
                break;
            case '--recursive':
                $RECURSIVE = true;
                break;
            case '--parse-only':
                $PARSE_ONLY = true;
                break;
            case '--int-only':
                $INT_ONLY = true;
                break;
            case '--verbose':
                $VERBOSE = true;
                break;
            default:
                $arg_array[$j++] = $argv[$i];
                break;
        }
    }

    foreach ($arg_array as $argument) {
        if (preg_match("/^[\-\-directory]+[=]+[0-9a-zA-Z\-\/.]+$/", $argument)) {
            if ($DIRECTORY == "") {
                $split = explode('=', $argument);
                $DIRECTORY = $split[1];
            } else {
                test_exit(10, "parametr '--directory' zadan vicekrat");
            }
        } else if (preg_match("/^[\-\-parse\-script]+[=]+[0-9a-zA-Z\-\/.]+$/", $argument)) {
            if ($PARSE_SCRIPT == "") {
                $split = explode('=', $argument);
                $PARSE_SCRIPT = $split[1];
            } else {
                test_exit(10, "parametr '\-\-parse-script' zadan vicekrat");
            }
        } else if (preg_match("/^[\-\-int\-script]+[=]+[0-9a-zA-Z\-\/.]+$/", $argument)) {
            if ($INT_SCRIPT == "") {
                $split = explode('=', $argument);
                $INT_SCRIPT = $split[1];
            } else {
                test_exit(10, "parametr '--int-script' zadan vicekrat");
            }
        } else if (preg_match("/^[\-\-jexamxml]+[=]+[0-9a-zA-Z\-\/.]+$/", $argument)) {
            if ($JEXAMXML == "") {
                $split = explode('=', $argument);
                $JEXAMXML = $split[1];
            } else {
                test_exit(10, "parametr '--jexamxml' zadan vicekrat");
            }
        } else if (preg_match("/^[\-\-jexamcfg]+[=]+[0-9a-zA-Z\-\/.]+$/", $argument)) {
            if ($JEXAMCFG == "") {
                $split = explode('=', $argument);
                $JEXAMCFG = $split[1];
            } else {
                test_exit(10, "parametr '--jexamcfg' zadan vicekrat");
            }
        } else {
            test_exit(10, "spatny paramametr skriptu ci spatne pouziti parametru (vice v '--help')");
        }
    }  

    if ($PARSE_ONLY && ($INT_ONLY || $INT_SCRIPT != ""))
        test_exit(10, "parametr --parse-only se nesmi kombinovat s parametrem --int-only nebo --int-script");
    if ($INT_ONLY && ($PARSE_ONLY || $PARSE_SCRIPT != ""))
        test_exit(10, "parametr --int-only se nesmi kombinovat s parametrem --parse-only nebo --parse-script");
    if ($DIRECTORY == "") $DIRECTORY = $CWD;
    if ($PARSE_SCRIPT == "") $PARSE_SCRIPT = "./parse.php";
    if ($INT_SCRIPT == "") $INT_SCRIPT = "./interpret.py";
    if ($JEXAMXML == "") $JEXAMXML = "/pub/courses/ipp/jexamxml/jexamxml.jar";
    if ($JEXAMCFG == "") $JEXAMCFG = "/pub/courses/ipp/jexamxml/options";
}

/*
*   Zkontroluje vstupy.
*/
function checkInput() {
    global $INT_ONLY;
    global $PARSE_ONLY;
    global $PARSE_SCRIPT;
    global $INT_SCRIPT;
    global $DIRECTORY;
    global $JEXAMXML;
    global $JEXAMCFG;
    
    if ($INT_ONLY || !$PARSE_ONLY) {
        if (!file_exists($INT_SCRIPT))
            test_exit(41, "skript interpretu IPPcode21 neexistuje (viz --help a --int-script)");
    }
    if ($PARSE_ONLY || !$INT_ONLY) {
        if (!file_exists($PARSE_SCRIPT))
            test_exit(41, "skript parseru IPPcode21 neexistuje (viz --help a --parse-script)");
    }
    if (!is_dir($DIRECTORY))
        test_exit(41, "umisteni '$DIRECTORY' neexistuje nebo neni pristupne");
    if (!file_exists($JEXAMXML))
        test_exit(41, "JAR balicek nastroje A7Soft JExamXML neexistuje (viz --help a --jexamxml)");
    if (!file_exists($JEXAMCFG))
        test_exit(41, "Konfiguracni soubor nastroje A7Soft JExamXML neexistuje (viz --help a --jexamcfg)");
}

/*
*   Otestuje interpret / parser podle argumentu
*/
function test() {
    global $DIRECTORY;
    global $CWD;
    global $TESTS_CNT;
    global $TESTS_FILES;
    global $TESTS_INV;
    global $TESTS_PASSED_CNT;
    global $TESTS_FAILED_CNT;
    global $PARSE_SCRIPT;
    global $INT_SCRIPT;
    global $PARSE_ONLY;
    global $INT_ONLY;
    global $JEXAMCFG;
    global $JEXAMXML;

    $TESTS_FILES = test_index($DIRECTORY);
    $TESTS_CNT = count($TESTS_FILES);
    test_checkFiles();
    $TESTS_CNT -= count($TESTS_INV);

    $skipped = 0;
    if (count($TESTS_FILES) == 0)
        fprintf(STDERR, "Varovani: nenalezen zadny test v zadane slozce\n");
    for ($i = 0; $i < count($TESTS_FILES); $i++) {
        $test_i = $i + 1 - $skipped;
        $all_tests = count($TESTS_FILES);
        verb_print("\rProbiha testovani ... (test $test_i/$all_tests)");
        $skip = false;
        $test = $TESTS_FILES[$i];
        $src_path = realpath($test[1] . DIRECTORY_SEPARATOR . $test[0] . ".src");
        $in_path = realpath($test[1] . DIRECTORY_SEPARATOR . $test[0] . ".in");
        $rc_path = realpath($test[1] . DIRECTORY_SEPARATOR . $test[0] . ".rc");
        $out_path = realpath($test[1] . DIRECTORY_SEPARATOR . $test[0] . ".out");

        foreach ($TESTS_INV as $invalid) {
            if ($invalid == $i)
                $skip = true;
        }

        if ($skip) {
            test_addFailed($i, 2);
            $out_diff = "";
            $rc = 0;
            $out = "";
            $skipped++;
            continue;
        }

        $out = "";
        $rc = 0;
        if ($PARSE_ONLY || !$INT_ONLY) {
            exec("php7.4 $PARSE_SCRIPT <$src_path 2>/dev/null", $out, $rc);
        }
        if (!$PARSE_ONLY && !$INT_ONLY) {
            $parser_out = fopen("/tmp/parser_output", "w");
            if (count($out) == 0)
                $out[0] = "";
            foreach($out as $write) {
                fwrite($parser_out, $write);
            }
            fclose($parser_out);
            exec("python3 $INT_SCRIPT --input=$in_path 2>/dev/null </tmp/parser_output", $out, $rc);
            unlink("/tmp/parser_output");
        } else if ($INT_ONLY || !$PARSE_ONLY) {
            $source = $src_path;
            exec("python3 $INT_SCRIPT --input=$in_path 2>/dev/null <$source", $out, $rc);
        }
        $ref_rc_f = fopen($rc_path, "r");
        $ref_rc = fgets($ref_rc_f);
        $ref_rc = intval($ref_rc);
        if ($ref_rc != $rc) {
            test_addFailed($i, 0, array($ref_rc, $rc));
            $out_diff = "";
            $rc = 0;
            $out = "";
            continue;
        }
        fclose($ref_rc_f);
        
        $out_f = fopen("/tmp/test_php_output", "a");
        if (count($out) == 0)
            $out[0] = "";
        foreach($out as $write) {
            fwrite($out_f, $write);
        }
        fclose($out_f);
        
        if ($PARSE_ONLY) {
            exec("java -jar $JEXAMXML /tmp/test_php_output $out_path $JEXAMCFG", $out, $rc);
            if (!$rc) {
                test_addFailed($i, 1);
                unlink("/tmp/test_php_output");
                $out_diff = "";
                $rc = 0;
                $out = "";
                continue;
            }
        } else {
            exec("diff /tmp/test_php_output $out_path", $out_diff, $rc);
            if (count($out_diff) && !$rc) {
                $diff = "";
                foreach($out_diff as $text)
                    $diff = $diff . $text;
                test_addFailed($i, 1, array($diff, 0));
                continue;
            }
        }

        unlink("/tmp/test_php_output");
        $out_diff = "";
        $rc = 0;
        $out = "";
    }
    if (count($TESTS_FILES) > 0)
        verb_print("\n");
    $TESTS_PASSED_CNT = $TESTS_CNT - $TESTS_FAILED_CNT;
}

/*
*   Prida do pole testy - dvojice nazev testu a cesta
*/
function test_index($DIRECTORY, &$results = array()) {
    global $RECURSIVE;
    $files = scandir($DIRECTORY);

    foreach ($files as $key => $value) {
        $path = realpath($DIRECTORY . DIRECTORY_SEPARATOR . $value);
        $fpath = realpath($DIRECTORY);
        if (!is_dir($path)) {
            $expl = explode('/', $path);
            $fname = end($expl);
            $testname = explode('.', $fname);
            $last_res = end($results);
            if (!$last_res || strcmp($last_res[0], $testname[0]))
                $results[] = array($testname[0], $fpath);
        } else if ($value != "." && $value != ".." && $RECURSIVE) {
            test_index($path, $results);
        }
    }

    return $results;
}

/*
*   Zkontroluje soubory jednotlivych testu, prip. vytvori in/out/rc
*/
function test_checkFiles() {
    global $TESTS_FILES;
    global $TESTS_INV;
    $i = 0;
    foreach ($TESTS_FILES as $test) {
        $path = $test[1] . DIRECTORY_SEPARATOR . $test[0];
        if (!is_file($path . ".src")) {
            fprintf(STDERR, "Varovani: '$test[0]' (umisteny v '$test[1]') neni validnim testem a nebude zahrnut do testovani (chybi .src)\n");
            array_push($TESTS_INV, $i);
        }
        if (!is_file($path . ".in")) {
            $f = fopen($path . ".in", "w");
            fclose($f);
        }
        if (!is_file($path . ".out")) {
            $f = fopen($path . ".out", "w");
            fclose($f);
        }
        if (!is_file($path . ".rc")) {
            $f = fopen($path . ".rc", "w");
            fwrite($f, "0");
            fclose($f);
        }
        $i++;
    }
}

/*
*   Prida do pole neprosly test s oduvodnenim.
*       reason: 0 -> return kod     1 -> vystupy se lisi    2 -> test je neplatny
*/
function test_addFailed($testIndex, $reason, $rcs = null) {
    global $TESTS_FAILED;
    global $TESTS_FAILED_CNT;
    if ($reason != 2)
        $TESTS_FAILED_CNT++;

    $reason_str = "";
    if ($rcs == null) {
        $rcs[0] = "<neznámý>";
        $rcs[1] = "<neznámý>";
    }

    switch($reason) {
        case 0:
            $reason_str = "Neočekávaný návratový kód $rcs[1]. Očekáváno: $rcs[0].";
            break;
        case 1:
            $reason_str = "Referenční výstup a výstup testovaného skriptu se liší.";
            break;
        default:
            $reason_str = "Neznámá chyba.";
            break;
    }

    if ($reason != 2)
        array_push($TESTS_FAILED, array($testIndex, $reason_str));
}

function generateHTML() {
    global $TESTS_CNT;
    global $TESTS_INV;
    global $TESTS_PASSED_CNT;
    global $TESTS_FAILED_CNT;
    global $TESTS_FAILED;
    global $TESTS_FILES;
    global $DIRECTORY;
    global $INT_SCRIPT;
    global $PARSE_SCRIPT;
    global $INT_ONLY;
    global $PARSE_ONLY;
    global $RECURSIVE;

    verb_print("Generovani HTML ...\n");
    if ($INT_ONLY)
        $TYPE = "pouze interpret";
    else if ($PARSE_ONLY)
        $TYPE = "pouze parser";
    else
        $TYPE = "parser a interpret";
    
    if ($RECURSIVE)
        $REC_STR = "ano";
    else
        $REC_STR = "ne";

    if ($TESTS_CNT != 0) {
        $passed_perc = ((float)$TESTS_PASSED_CNT / (float)$TESTS_CNT)*100.0;
        $failed_perc = ((float)$TESTS_FAILED_CNT / (float)$TESTS_CNT)*100.0;
    } else {
        $passed_perc = 0;
        $failed_perc = 0;
    }
    
    printf('<!DOCTYPE html>
    <html style="font-size: 16px;">
      <head>
        <title>Testy IPPcode21</title>
      </head>
      <style>
        thead {background-color: gainsboro; height: 60px;}
        tbody {color: black; height: 45px;}
        table {border-collapse: collapse;}
        p {margin-bottom: 0px; margin-top: 7px;}
        tab1 { padding-left: 1em; }
      </style>
      <body>
        <section>
          <div>
            ');
    printf('
            <h1>Výsledky testů</h1>
            <p>Tato stránka je výstupem skriptu, který testuje parsování či interpretaci jazyka IPPcode21. Nastavení je možno měnit pomocí parametrů zadaných při spouštění 
            skriptu \'test.php\'. Pokud se nějaký test neprovedl, znamená to, že nebyl nalezen *.src (zdrojový) soubor daného testu. Do celkového počtu testů v souhrnu
            se tyto neprovedené testy nepočítají.
            </p>
            <br>
            <h4><b>Zvolené nastavení</b>
            </h4>
            <div class="item">
            <p style="text-indent: 7px;">Adresář: <tab1>%s</tab1></p>
            <p style="text-indent: 7px;">Rekurzivní prohledávání adresáře: <tab1>%s</tab1></p>
            <p style="text-indent: 7px;">Parsovací skript: <tab1>%s</tab1></p>
            <p style="text-indent: 7px;">Skript interpretu: <tab1>%s</tab1></p>
            <p style="text-indent: 7px;">Typ testů: <tab1>%s</tab1></p>
            </div>
            <br>
            ', $DIRECTORY, $REC_STR, $PARSE_SCRIPT, $INT_SCRIPT, $TYPE);
    printf('
            <h4><b>Souhrn</b>
            </h4>
            <p style="text-indent: 7px;">Celkem testů: <tab1>%d</tab1></p>
            <p style="text-indent: 7px;">Uspělo: <tab1>%d</tab1> <tab1>(%.2f %%)</tab1></p>
            <p style="text-indent: 7px;">Neuspělo: <tab1>%d</tab1> <tab1>(%.2f %%)</tab1></p>
            <p style="text-indent: 7px;">Neprovedeno: <tab1>%d</tab1></p>
            <br>
            <br>
            <br>
            <br>
            ', $TESTS_CNT, $TESTS_PASSED_CNT, $passed_perc, $TESTS_FAILED_CNT, $failed_perc, count($TESTS_INV));
    printf('
            <div>
              <center>
              <table style="width: 95%%; align-content: center;">
                <colgroup>
                  <col width="4%%">
                  <col width="15%%">
                  <col width="38%%">
                  <col width="33%%">
                  <col width="10%%">
                </colgroup>
                <thead>
                  <tr>
                    <td style="text-align: center;">#</td>
                    <td style="text-indent: 10px;"><h3>Název</h3></td>
                    <td style="text-indent: 10px;"><h3>Adresář</h3></td>
                    <td style="text-indent: 10px;"><h3>Poznámka</h3></td>
                    <td style="text-indent: 10px;"><h3>Výsledek</h3></td>
                  </tr>
                </thead>
            ');
    $i = 0;
    foreach ($TESTS_FILES as $test) {
        $print = true;
        $result = "Uspěl";
        $note = " ";
        foreach($TESTS_FAILED as $failed) {
            if ($i == $failed[0]) {
                $result = "Neuspěl";
                $note = $failed[1];
            }
        }
        foreach($TESTS_INV as $invalid) {
            if ($i == $invalid) {
                $result = "Neproveden";
                $note = "Neplatný test";
            }
        }
        
        if ($print)
            generateHTML_test($i++ + 1, $test[0], $test[1], $note, $result);
    }
    printf('          </table>
              </center>
            </div>
          </div>
        </section>
      </body>
    </html>'
    );
}


/*
*   Generuje HTML kod jednotliveho radku-testu v tabulce
*/
function generateHTML_test($i, $testname, $testdir, $testnote, $testresult) {
    global $TESTS_CNT;
    printf('
            <tbody>
                  <tr>
                    <tr>
                      <td style="text-align: center;"><p>%s</p></td>
                      <td style="text-indent: 6px;"><p>%s</p></td>
                      <td style="text-indent: 6px;"><p>%s</p></td>
                      <td style="text-indent: 6px;"><p>%s</p></td>
                      <td style="text-indent: 6px;"><p>%s</p></td>
                    </tr>
                  </tr>
                </tbody>
            ', $i, $testname, $testdir, $testnote, $testresult);
}

function verb_print($text) {
    global $VERBOSE;
    if ($VERBOSE)
        fprintf(STDERR, $text);
}

?>