@echo off
cd script
title Deleted Accounts
echo #################################
echo  Deleted Accounts
echo #################################
echo.
echo # Example usage: 
echo deleteAccounts.py -b http://account.com -u admin@account.com -p 1234 -a accounts.txt -r report [-d 6]
echo.
: execute
echo # Insert required parameters:
set /p cmd=
%cmd%
goto execute
