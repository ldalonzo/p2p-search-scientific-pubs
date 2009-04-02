--------------------------------------------------------------------------------------------
A) How to configure the local directory to index (which contains the articles in PDF format)
--------------------------------------------------------------------------------------------
Add the directory path that you would like to be indexed in the function directoriesToIndex in the class Indexer
(line 271 in main.py). Note that the client needs to be restarted.

--------------------------------------------------------------------------------------------
B) How to configure django templates
--------------------------------------------------------------------------------------------
In the TEMPLATE_DIRS section (line 69) add the ABSOLUTE path (in your local filesystem) of the django templates.
Their relative position is /src/mysite/django-templates

----------------------------------------------------------------------------------------------------------------
C) How to start:
----------------------------------------------------------------------------------------------------------------

1) start the superpeer with:

   python superpeer.py if=IFNAME

   where IFNAME is the name of the network interface (as you can see from the output of ifconfig). The superpeer
   will run at that address at port 15000

2) start the peer with:

        ./start -alias NICKNAME -ip IPADDRESS -sp SPIPADDRESS -djp PORT

   e.g. ./start -alias leo -ip 130.161.158.167 -sp 130.161.158.167 -djp 9000

   where NICKNAME is a unique alias that identifies the peer, IPADDRESS is the network address of your machine,
   SPIPADDRESS is the network address of the superPeer and PORT is the port in which the django web server run.

3) open your favourite web browser and go to http://localhost:PORT

--------------------------------------------------------------------------------------------
D) Package structure:
--------------------------------------------------------------------------------------------
/clustering
	

/common

/core

/index

/repo

/logs

/main

/mysite
	contains the django modules for rendering the results as html and query the system.

/pdfparser
	pdf parser

-------------------------------------------------------------------------------------------------
E) Dependencies:
------------------------------------------------------------------------------------------------

	numpy     (http://sourceforge.net/project/showfiles.php?group_id=1369&package_id=175103)
	django    (http://www.djangoproject.com/download/1.0.2/tarball/)
	PyCluster (http://bonsai.ims.u-tokyo.ac.jp/~mdehoon/software/cluster/Pycluster-1.44.tar.gz)
        pdftohtml (version 0.36)
		you need to compile the source for your architecture and move the binary file into
                /lib/pdftohtml-0.36

        (Only if the citation feature is enabled)
	ParsCit

-------------------------------------------------------------------------------------------------
F) You can choose to enable/disable the automatic citation features:
-------------------------------------------------------------------------------------------------

	function feed() @ class PDFPaperParserHtml (module PDFPaperParser.py) line 65
	
        htmlparser.getMetadata(True)     # for enabling reference string parsing
        htmlparser.getMetadata(False)    # for disable

	The reference string parsing is done by ParsCit, a reference string parsing package written in Perl. It performs
        very slowly because I call a Perl interpreter for each reference string to parse.

-------.------------------------------------------------------------------------------------
G) Known problems
--------------------------------------------------------------------------------------------
There is some problem with the thread during the shutdown (i.e. the childs threads doesn't join with the main thread.
For this reason you must be sure to kill all the process (you can just kill .start.sh) if you are going to
stop & restart the program.

I used xmlrpclib for let the peers to communicate between each other.

The main does the following things:

	0) The Index is the shared object in which all the process deal with. When this object it is created,
           it looks into the /repo folder and tries to restore the data into the memory. Notice that solution
           works if the collection is quite small. It should be considered to use a relational database.

	1) Indexer process
		It index all the files specified (cfr. 2) if they have not been already known to the system

	2) PeerServerProcess

	3) ClusteringProcess





