ParsCit README

This software is copyrighted 2008 by Min-Yen Kan, Isaac G. Councill
and C. Lee Giles.  This program and all its source code is distributed
are under the terms of the GNU General Public License (or the Lesser
GPL).

    ParsCit is free software: you can redistribute it and/or modify it
    under the terms of the GNU Lesser General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    ParsCit is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with ParsCit.  If not, see
    <http://www.gnu.org/licenses/>.

See INSTALL.txt and USAGE.txt for more information.
CHANGELOG.txt for updates on code and model changes.
Also see doc/index.html for the web page describing this project.

----------------------------------------------------------------------
Files:

bin/		- Binaries / scripts for running ParsCit
   /archtest.pl		- ?
   /citeExtract.pl 	- Script for running the whole pipeline from a text file (body/references segmentation, reference string parsing)
   /segmentCitations.pl	- Script for running reference string parsing only.  Receives a set of reference strings (one on each line) and parses them.
   /parsecit-client.pl	- Original perl web service client (tested at IST)
   /parsecit-server.pl	- Original perl web service server (tested at IST)
   /ParsCitClient.rb	- Ruby web service client (tested at NUS)
   /ParsCitServer.rb	- Ruby web service server (tested at NUS)
   /redo.pl		- Cross Validation training script and training notes (at end of script)
CHANGELOG.TXT	- Changes between versions of the code.
crfpp/		- The CRF++ machine learning package used within ParsCit
     /traindata	- Sample training data for the CRF++ code
demodata/	- Test data for sanity checking outputs
doc/		- The CGI base installation and documentation (scientific publications) about ParsCit
INSTALL.TXT	- installation and basic instructions
lib/		- perl libraries for ParsCit 
   /cgiLog.txt	- CGI log for running web interface (nb, different than web service interface)
README.TXT	- this file
resources/	- dictionary files and CRF++ trained models
tmp/		- guess! :-)
USAGE.TXT	- Usage files for the citeExtract and web service interface 
wsdl/		- The web service description language file 

