## read damper
## Update the id for your point
curl -X "POST" "http://localhost/api/read" \
     -H 'Accept: application/json' \
     -H 'Content-Type: text/zinc' \
     -d $'ver:"2.0" 
filter,limit 
"id==@52e40666-a939-49ce-b403-ea08247b379d",1000
'
