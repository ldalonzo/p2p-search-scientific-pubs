# File: Makefile
SHELL           = /bin/sh
PROJECT         = thesis

.PHONY          = all clean

all: pdf

pdf: $(PROJECT).pdf

view: $(PROJECT).pdf
	acroread $(<)

%.pdf: %.tex Makefile *.tex *.sty
	pdflatex -interaction=nonstopmode $(<)
	-bibtex $(PROJECT)
	pdflatex -interaction=nonstopmode $(<)
	pdflatex -interaction=nonstopmode $(<)

force:
	$(MAKE) -W $(PROJECT).tex

clean:
	rm -f *.{out,brf,toc,lof,bbl,blg,bak,aux,dvi,ps,log} *~
	rm -f */*.{out,brf,toc,lof,bbl,blg,bak,aux,dvi,ps,log} */*~

dist: pdf clean
	( cd .. ; \
	rm -rf thesis-style_`date +%Y%m%d`.zip ; \
	zip -r thesis-style_`date +%Y%m%d`.zip thesis-style -x \*/.svn/\* \*/auto/\*   )
	cp thesis.pdf ../thesis-style_`date +%Y%m%d`.pdf