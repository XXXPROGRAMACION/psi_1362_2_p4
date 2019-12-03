rm coverage.txt
touch coverage.txt

echo "Coverage of the datamodel application:" >> coverage.txt

coverage erase
coverage run --omit="*/test*" --source=datamodel ./manage.py test datamodel 
coverage report -m -i >> coverage.txt

echo "" >> coverage.txt
echo "" >> coverage.txt
echo "" >> coverage.txt
echo "Coverage of the logic application:" >> coverage.txt

coverage erase
coverage run --omit="*/test*" --source=logic ./manage.py test logic
coverage report -m -i >> coverage.txt