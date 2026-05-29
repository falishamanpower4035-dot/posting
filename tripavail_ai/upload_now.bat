@echo off
echo =====================================
echo   Uploading to Droplet...
echo =====================================
echo.
echo When prompted for password, enter: tRipavail1556--
echo.
pause
echo.

scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r smart_scheduler.py root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r bot.py root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r main.py root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r requirements.txt root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r .env root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r droplet_setup.sh root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r system_check.py root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r config root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r core root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r scripts root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r social_media root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r assets root@138.68.141.3:/opt/tripavail_ai/
scp -o PreferredAuthentications=password -o StrictHostKeyChecking=no -r data root@138.68.141.3:/opt/tripavail_ai/

echo.
echo =====================================
echo   Upload Complete!
echo =====================================
echo.
echo Now in your droplet terminal, run:
echo   cd /opt/tripavail_ai
echo   bash droplet_setup.sh
echo.
pause


