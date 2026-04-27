#!/usr/bin/env bash
# ANSI color demo: shows 8/16 colors, bold/italic/underline, 256-color and
# truecolor sequences so you can verify the log view renders them.

esc=$'\033'

echo "${esc}[1mBold${esc}[0m  ${esc}[3mItalic${esc}[0m  ${esc}[4mUnderline${esc}[0m"
echo

echo "8 base colors:"
for c in 30 31 32 33 34 35 36 37; do
    printf "${esc}[${c}m  %s  ${esc}[0m" "$c"
done
echo

echo "8 bright colors:"
for c in 90 91 92 93 94 95 96 97; do
    printf "${esc}[${c}m  %s  ${esc}[0m" "$c"
done
echo
echo

echo "256-color cube (sample):"
for c in 16 52 88 124 160 196 202 208 214 220 226 154 82 46 50 51 33 21 57 93 165 201; do
    printf "${esc}[38;5;${c}m█${esc}[0m"
done
echo
echo

echo "Truecolor gradient:"
for i in $(seq 0 5 255); do
    printf "${esc}[38;2;${i};128;$((255 - i))m█${esc}[0m"
done
echo
echo

echo "${esc}[1;31mERROR${esc}[0m: example error line"
echo "${esc}[1;33mWARNING${esc}[0m: example warning line"
echo "${esc}[1;32mOK${esc}[0m: example success line"
