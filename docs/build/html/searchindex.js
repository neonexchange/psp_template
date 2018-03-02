Search.setIndex({docnames:["blockchain/apps","blockchain/models","customer/dwolla","customer/models","index","install","license","nexpsp/settings","overview"],envversion:53,filenames:["blockchain/apps.rst","blockchain/models.rst","customer/dwolla.rst","customer/models.rst","index.rst","install.rst","license.rst","nexpsp/settings.rst","overview.rst"],objects:{"blockchain.apps":{BlockchainConfig:[0,1,1,""],check_deposit_and_tx:[0,4,1,""],create_move_to_main_tx:[0,4,1,""],create_transaction:[0,4,1,""],monitor_wallet_loop:[0,4,1,""],move_deposits_to_wallet:[0,4,1,""],on_blockchain_new_block:[0,4,1,""],process_bank_transfers:[0,4,1,""],process_crypto_purchases:[0,4,1,""],process_crypto_received_bank_transfers:[0,4,1,""],process_pending_blockchain_transactions:[0,4,1,""],process_possible_transaction_match:[0,4,1,""],refresh_dwolla_client_token:[0,4,1,""],start_blockchain:[0,4,1,""],update_crypto_prices:[0,4,1,""]},"blockchain.apps.BlockchainConfig":{name:[0,2,1,""],ready:[0,3,1,""]},"blockchain.models":{BlockchainTransfer:[1,1,1,""],DepositWallet:[1,1,1,""],Price:[1,1,1,""]},"blockchain.models.BlockchainTransfer":{DoesNotExist:[1,5,1,""],MultipleObjectsReturned:[1,5,1,""],amount:[1,2,1,""],asset:[1,2,1,""],confirmed_block:[1,2,1,""],deposit:[1,2,1,""],depositwallet:[1,2,1,""],from_address:[1,2,1,""],get_asset_display:[1,3,1,""],get_status_display:[1,3,1,""],id:[1,2,1,""],main_transfer:[1,2,1,""],neoscan_url:[1,2,1,""],objects:[1,2,1,""],purchase:[1,2,1,""],start_block:[1,2,1,""],status:[1,2,1,""],to_address:[1,2,1,""],transaction:[1,2,1,""],transaction_id:[1,2,1,""],tx_json:[1,2,1,""]},"blockchain.models.DepositWallet":{DoesNotExist:[1,5,1,""],MultipleObjectsReturned:[1,5,1,""],address:[1,2,1,""],create:[1,6,1,""],deposit:[1,2,1,""],depositor:[1,2,1,""],depositor_id:[1,2,1,""],id:[1,2,1,""],next_available_for_retrieval:[1,6,1,""],objects:[1,2,1,""],start_height:[1,2,1,""],transfer:[1,2,1,""],transfer_id:[1,2,1,""],transfer_to_main:[1,2,1,""],transfer_to_main_id:[1,2,1,""],wallet:[1,2,1,""],wallet_file:[1,2,1,""],wallet_pass:[1,2,1,""]},"blockchain.models.Price":{DoesNotExist:[1,5,1,""],MultipleObjectsReturned:[1,5,1,""],asset:[1,2,1,""],get_asset_display:[1,3,1,""],get_next_by_updated_at:[1,3,1,""],get_previous_by_updated_at:[1,3,1,""],id:[1,2,1,""],objects:[1,2,1,""],updated_at:[1,2,1,""],usd:[1,2,1,""]},"customer.dwolla":{DwollaClient:[2,1,1,""],dwolla_create_transfer:[2,4,1,""],dwolla_create_user:[2,4,1,""],dwolla_generate_funding_source_token:[2,4,1,""],dwolla_get_balance:[2,4,1,""],dwolla_get_funding_sources:[2,4,1,""],dwolla_get_transfers:[2,4,1,""],dwolla_get_url:[2,4,1,""],dwolla_get_user_balance:[2,4,1,""],dwolla_get_user_bank_accounts:[2,4,1,""],dwolla_send_to_user:[2,4,1,""],dwolla_simulate_sandbox_transfers:[2,4,1,""],dwolla_update_user:[2,4,1,""]},"customer.dwolla.DwollaClient":{__init__:[2,3,1,""],api_url:[2,2,1,""],client:[2,2,1,""],customer_url:[2,2,1,""],funding_source_url:[2,2,1,""],instance:[2,6,1,""],refresh:[2,3,1,""],token:[2,2,1,""]},"customer.models":{Deposit:[3,1,1,""],PSPUser:[3,1,1,""],PSPUserManager:[3,1,1,""],Purchase:[3,1,1,""],ReceiveableAccount:[3,1,1,""],on_pspuser_saved:[3,4,1,""]},"customer.models.Deposit":{DoesNotExist:[3,5,1,""],MultipleObjectsReturned:[3,5,1,""],amount:[3,2,1,""],asset:[3,2,1,""],blockchain_transfer:[3,2,1,""],blockchain_transfer_id:[3,2,1,""],date_created:[3,2,1,""],date_updated:[3,2,1,""],deposit_wallet:[3,2,1,""],deposit_wallet_id:[3,2,1,""],failure_reason:[3,2,1,""],fee:[3,2,1,""],gas_price:[3,2,1,""],get_asset_display:[3,3,1,""],get_next_by_date_created:[3,3,1,""],get_next_by_date_updated:[3,3,1,""],get_previous_by_date_created:[3,3,1,""],get_previous_by_date_updated:[3,3,1,""],get_status_display:[3,3,1,""],id:[3,2,1,""],invoice_id:[3,2,1,""],neo_sender_address:[3,2,1,""],objects:[3,2,1,""],pspuser_set:[3,2,1,""],receiver_account:[3,2,1,""],receiver_account_id:[3,2,1,""],sender_account_id:[3,2,1,""],status:[3,2,1,""],total:[3,2,1,""],total_fee:[3,2,1,""],total_gas:[3,2,1,""],transfer_id:[3,2,1,""],transfer_url:[3,2,1,""],user:[3,2,1,""],user_id:[3,2,1,""]},"customer.models.PSPUser":{DoesNotExist:[3,5,1,""],MultipleObjectsReturned:[3,5,1,""],REQUIRED_FIELDS:[3,2,1,""],USERNAME_FIELD:[3,2,1,""],address1:[3,2,1,""],address2:[3,2,1,""],city:[3,2,1,""],customer_type:[3,2,1,""],date_joined:[3,2,1,""],date_of_birth:[3,2,1,""],deposit_set:[3,2,1,""],depositwallet_set:[3,2,1,""],dwolla_id:[3,2,1,""],dwolla_url:[3,2,1,""],email:[3,2,1,""],first_name:[3,2,1,""],get_full_name:[3,3,1,""],get_next_by_date_joined:[3,3,1,""],get_next_by_date_of_birth:[3,3,1,""],get_next_by_last_login:[3,3,1,""],get_previous_by_date_joined:[3,3,1,""],get_previous_by_date_of_birth:[3,3,1,""],get_previous_by_last_login:[3,3,1,""],get_short_name:[3,3,1,""],get_state_display:[3,3,1,""],groups:[3,2,1,""],has_module_perms:[3,3,1,""],has_perm:[3,3,1,""],id:[3,2,1,""],is_admin:[3,2,1,""],is_seller:[3,2,1,""],is_staff:[3,2,1,""],last_name:[3,2,1,""],logentry_set:[3,2,1,""],objects:[3,2,1,""],pending_deposit:[3,2,1,""],pending_deposit_id:[3,2,1,""],postal_code:[3,2,1,""],purchase_set:[3,2,1,""],receiveableaccount_set:[3,2,1,""],ssn_lastfour:[3,2,1,""],state:[3,2,1,""],to_json:[3,3,1,""],to_update_json:[3,3,1,""],user_permissions:[3,2,1,""]},"customer.models.PSPUserManager":{create_superuser:[3,3,1,""],create_user:[3,3,1,""]},"customer.models.Purchase":{DoesNotExist:[3,5,1,""],MultipleObjectsReturned:[3,5,1,""],amount:[3,2,1,""],asset:[3,2,1,""],blockchain_transfer:[3,2,1,""],blockchain_transfer_id:[3,2,1,""],date_created:[3,2,1,""],date_updated:[3,2,1,""],failure_reason:[3,2,1,""],fee:[3,2,1,""],gas_price:[3,2,1,""],get_asset_display:[3,3,1,""],get_next_by_date_created:[3,3,1,""],get_next_by_date_updated:[3,3,1,""],get_previous_by_date_created:[3,3,1,""],get_previous_by_date_updated:[3,3,1,""],get_status_display:[3,3,1,""],id:[3,2,1,""],neo_address:[3,2,1,""],objects:[3,2,1,""],receiver_account_id:[3,2,1,""],sender_account_id:[3,2,1,""],status:[3,2,1,""],total:[3,2,1,""],total_fee:[3,2,1,""],total_gas:[3,2,1,""],transfer_url:[3,2,1,""],user:[3,2,1,""],user_id:[3,2,1,""]},"customer.models.ReceiveableAccount":{Default:[3,6,1,""],DoesNotExist:[3,5,1,""],MultipleObjectsReturned:[3,5,1,""],account_id:[3,2,1,""],customer_url:[3,2,1,""],funding_url:[3,2,1,""],id:[3,2,1,""],objects:[3,2,1,""],user:[3,2,1,""],user_id:[3,2,1,""]},blockchain:{apps:[0,0,0,"-"],models:[1,0,0,"-"]},customer:{dwolla:[2,0,0,"-"],models:[3,0,0,"-"]},nexpsp:{settings:[7,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","attribute","Python attribute"],"3":["py","method","Python method"],"4":["py","function","Python function"],"5":["py","exception","Python exception"],"6":["py","staticmethod","Python static method"]},objtypes:{"0":"py:module","1":"py:class","2":"py:attribute","3":"py:method","4":"py:function","5":"py:exception","6":"py:staticmethod"},terms:{"case":0,"class":[0,1,2,3],"default":3,"function":2,"return":[0,1,2,3],"static":[1,2,3],"true":[1,3],And:0,For:[0,7],GAS:0,Gas:[0,3,4,8],One:0,That:2,The:[0,1,2,3,4,8],Then:[0,5],There:3,These:0,__init__:2,abl:5,accept:8,access:[1,3],accessor:2,accordingli:0,account:[2,3],account_id:3,ach:[2,4,8],activ:[3,5],added:0,address1:3,address2:3,address:[1,3],admin:[3,7],after:0,all:[0,2,3],also:[0,1,5],amount:[0,1,2,3],ani:[0,2,3],anoth:[1,4,8],api:[2,3,4,8],api_url:2,app:[3,4],app_label:3,app_modul:0,app_nam:0,applic:7,arg:[1,3],asset:[1,3],assign:3,associ:[0,1,2,3],associatd:3,async:0,attribut:0,author:6,autofield:[1,3],autogener:[1,3],back:0,balanc:[0,2],bank:[0,2,3,4,8],base:[0,1,2,3,8],basic:[0,2],basket:0,batch:0,been:[0,2,3],befor:0,belong:3,below:[],bin:5,birth:3,block:[0,1],blockchain:[3,4,7],blockchain_transf:3,blockchain_transfer_id:3,blockchainconfig:0,blockchaintransf:[0,1,3],bool:[2,3],booleanfield:3,both:[1,4,8],browser:5,built:[],bytearrai:1,calcul:0,call:0,can:[0,1,5],chain:0,chang:0,charfield:[1,3],check:[0,3],check_deposit_and_tx:0,child:[],children:[],citi:3,clear:0,client:2,clone:5,closer:0,cmc:0,code:3,com:[6,7],command:5,compar:0,complet:[0,5],confirm:1,confirmed_block:1,conform:3,consum:3,convent:3,core:[0,1],could:0,creat:[0,1,2,3],create_forward_many_to_many_manag:[],create_move_to_main_tx:0,create_superus:3,create_transact:0,create_us:3,creation:2,crypto:[0,1,2,3],currenc:1,current:[0,4],custom:[0,1,4],customer_typ:3,customer_url:[2,3],date:3,date_cr:3,date_join:3,date_of_birth:3,date_upd:3,datefield:3,datetimefield:[1,3],defer:[],defin:[],deleg:[],deposit:[0,1,2,3],deposit_set:3,deposit_wallet:[0,3],deposit_wallet_id:3,depositor:[0,1,3],depositor_id:1,depositwallet:[1,3],depositwallet_set:3,design:3,detail:[0,1,2,3],determin:[2,3],dict:[1,2,3],dictionari:2,differ:1,directori:5,django:[0,1,3,7],djangoproject:7,doc:7,doe:[2,3,4],doesnotexist:[1,3],doing:0,don:0,done:0,dwolla:[0,3,4,7,8],dwolla_create_transf:2,dwolla_create_us:2,dwolla_generate_funding_source_token:2,dwolla_get_bal:2,dwolla_get_funding_sourc:2,dwolla_get_transf:2,dwolla_get_url:2,dwolla_get_user_bal:2,dwolla_get_user_bank_account:2,dwolla_id:3,dwolla_send_to_us:2,dwolla_simulate_sandbox_transf:2,dwolla_update_us:2,dwolla_url:3,dwollacli:2,dynam:[],each:[0,3],easili:[4,8],email:3,emailfield:3,endpoint:2,environ:5,event:[0,3],everi:0,exampl:[4,8],except:[1,3],exchang:[1,3,6],execut:[],explicitli:[3,5],failur:3,failure_reason:3,fals:[1,3],fashion:0,fee:3,fiat:[0,1,2,3,4,8],field:[1,3],file:[1,7],filepathfield:1,find:[1,3],finish:[0,1],first:3,first_nam:3,floatfield:[1,3],follow:[0,1,2,3,5],foreignkei:[1,3],format:3,forward:[],forwardmanytoonedescriptor:[],forwardonetoonedescriptor:[],found:0,from:[0,1,2,4,8],from_address:1,full:[3,7],fund:[2,3],funding_sourc:2,funding_source_url:2,funding_url:3,gas:3,gas_pric:3,gener:[2,7],get:[0,2,3],get_asset_displai:[1,3],get_full_nam:3,get_next_by_date_cr:3,get_next_by_date_join:3,get_next_by_date_of_birth:3,get_next_by_date_upd:3,get_next_by_last_login:3,get_next_by_updated_at:1,get_previous_by_date_cr:3,get_previous_by_date_join:3,get_previous_by_date_of_birth:3,get_previous_by_date_upd:3,get_previous_by_last_login:3,get_previous_by_updated_at:1,get_short_nam:3,get_state_displai:3,get_status_displai:[1,3],github:6,given:3,grant:3,greater:0,group:3,has:[0,1,2,3],has_module_perm:3,has_perm:3,have:[0,3],height:1,helper:2,here:0,http:[0,5,6,7],ideal:0,identifi:0,implement:[0,1,2,3,4,8],incom:0,indic:0,inform:[2,7],inherit:3,initi:[0,2],instal:4,instanc:[0,1,2,3],integerfield:1,interest:0,interfact:[4,8],invoic:[0,3],invoice_id:3,is_act:3,is_admin:3,is_next:[1,3],is_sel:3,is_staff:3,is_superus:3,its:0,join:3,json:[1,3],just:[0,3],kind:3,know:0,kwarg:[1,3],label:[1,3],last:3,last_login:3,last_nam:3,lastfour:3,later:5,licens:4,list:[2,7],load:[],local:[0,5],localflavor:3,localhuman:[],log:0,logentri:3,logentry_set:3,login:3,look:0,loop:0,m2m:3,main:[0,1,3,6,7],main_transf:1,make:5,manag:[1,3,5],mani:[],manual:4,manytomanydescriptor:[],manytomanyfield:3,mark:0,match:0,method:[0,2],minut:0,mit:6,mode:2,model:[0,2,4],monitor:[0,1],monitor_wallet_loop:0,more:[0,7],most:[],move:0,move_deposits_to_wallet:0,multipleobjectsreturn:[1,3],name:[0,3],navig:5,need:[0,3,5],neighbor:5,neo:[0,1,3,4,8],neo_address:3,neo_sender_address:3,neon:6,neonexchang:6,neoscan_url:1,network:8,newli:0,nex:[5,8],nexpsp:4,next:[0,1,3],next_available_for_retriev:1,none:3,noreload:5,normal:3,note:[0,2],now:5,number:0,obj:3,object:[0,1,2,3],on_blockchain_new_block:0,on_pspuser_sav:3,onc:[0,5],one:[0,1,3],onetoonefield:[1,3],onli:3,open:6,oper:2,our:0,out:0,outgo:0,output:[0,3],overview:4,owed:0,paid:0,param:[0,1],paramet:[0,1,2,3],parent:[],pass:1,password:3,payment:8,peewe:[0,1],pend:[0,3],pending_deposit:3,pending_deposit_id:3,perm:3,permiss:3,persist:3,pip:5,pizza:[],place:[],platform:[4,8],postal:3,postal_cod:3,previou:[1,3],price:[0,1,3],process:[0,1],process_bank_transf:0,process_crypto_purchas:0,process_crypto_received_bank_transf:0,process_pending_blockchain_transact:0,process_possible_transaction_match:0,project:[4,5,7,8],provid:8,psp:[0,2,3,4,5,8],pspuser:[1,2,3],pspuser_set:3,pspusermanag:3,purchas:[0,1,2,3],purchase_set:3,python3:5,python:4,queri:[],reactor:0,read:[],readi:0,reason:3,receiev:0,receiv:[0,3,4,8],receivableaccount:3,receiveableaccount:3,receiveableaccount_set:3,receiver_account:3,receiver_account_id:3,reciev:3,ref:7,refresh:[0,2],refresh_dwolla_client_token:0,relat:[],related_nam:[],remark3:0,remark:0,replac:[4,8],repositori:5,repres:[0,1,3],represent:1,request:0,requir:5,required_field:3,respons:2,restaur:[],retreiv:2,retriev:[1,2,3],retur:3,revers:[],reversemanytoonedescriptor:[],reverseonetoonedescriptor:[],run:0,runserv:5,sandbox:2,save:3,scan:1,see:[3,7],sell:1,seller:3,send:[1,2,3,4,8],sender:3,sender_account_id:3,sent:2,server:4,servic:8,set:[0,4],should:[3,4,5,8],show:[1,3],side:[],simul:[0,2],singleton:[2,3],some:0,someth:0,sourc:[0,1,2,3,5,6],specif:3,ssn:3,ssn_lastfour:3,staff:3,start:[0,1,4],start_block:1,start_blockchain:0,start_height:1,startproject:7,state:[0,3,4,8],statu:[0,1,3],str:[1,2,3],subclass:[],success:2,sudo:5,superus:3,system:[0,1,3],take:[0,2],templat:8,temporari:[0,1],than:0,thei:[0,1,3],them:[0,1,2,3,8],thi:[0,1,2,3,4,5,7,8],thing:0,those:8,through:0,time:0,to_address:1,to_json:3,to_update_json:3,token:[0,2],top:[],topic:7,total:3,total_fe:3,total_ga:3,tranfer:[4,8],transact:[0,1],transaction_id:1,transactionattributeusag:0,transfer:[0,1,2,3,4,8],transfer_id:[1,3],transfer_to_main:1,transfer_to_main_id:1,transfer_url:3,twist:0,tx_json:1,txattrubuteusag:0,txt:5,type:[0,1,2,3],unit:[4,8],upat:0,updat:[0,1,2,3],update_crypto_pric:0,updated_at:1,url:[1,2,3],urlfield:3,usd:1,use:[0,2],used:[1,2,3],user:[0,1,2,3,4,8],user_id:3,user_permiss:3,username_field:3,userwallet:[0,1],uses:[4,8],using:7,usr:5,usstatefield:3,uszipcodefield:3,uuidfield:3,valu:[1,7],venv:5,version:5,via:[0,5,8],view:[1,3],virtual:5,virtualenv:5,visit:5,wait:0,wallet:[0,1,3],wallet_fil:1,wallet_pass:1,want:0,websit:3,well:0,what:[0,1,2,3,4],when:[0,1,3],where:1,whether:3,which:0,who:0,wish:0,without:3,wont:0,work:2,would:0,wrapper:[],you:[0,5],your:[0,5],zero:0},titles:["blockchain.apps","blockchain.models","customer.dwolla","customer.models","NEX Payment Service Provider Template","Installation","License","nexpsp.settings","Overview"],titleterms:{app:0,blockchain:[0,1],compil:[],current:8,custom:[2,3],doe:8,dwolla:2,instal:5,licens:6,machin:[],manual:5,model:[1,3],neo:5,nex:4,nexpsp:7,overview:8,payment:4,provid:4,python:5,server:5,servic:4,set:7,start:5,templat:4,virtual:[],what:8}})