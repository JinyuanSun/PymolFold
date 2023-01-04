from pymol import cmd, stored
 
def listselection (selection, output="N", HOH="Y"):
	"""	
	usage: listselection selection, [output=N/S/P, [HOH=Y/N ]]
	
	More information at: PymolWiki: http://http://pymolwiki.org/index.php/ListSelection2
	AUTHOR: Pietro Gatti-Lafranconi, 2013
	Please inform me if you use/improve/like/dislike/publish with this script.
	CC BY-NC-SA
	"""
	printedselection=""
	extra=""
	counter=0
	sel=selection
	objs=cmd.get_object_list(sel)

	if HOH=="N":
		sel=selection+" and not resn HOH"
		extra=", without HOH"
	
	for a in range(len(objs)):
		m1=cmd.get_model(sel+" and "+objs[a])
		for x in range(len(m1.atom)):
			if m1.atom[x-1].resi!=m1.atom[x].resi:
				printedselection+="%s/%s/%s/%s\n" % (objs[a], m1.atom[x].chain, m1.atom[x].resn, m1.atom[x].resi)
				counter+=1
				
	print "Residues in '%s%s': %s" % (selection, extra, counter)
	if output=="S": print printedselection
	if output=="P":
		f=open('listselection_'+selection+'.txt','w')
		f.write("Residues in '%s%s': %s\n" % (selection, extra, counter))
		f.write(printedselection)
		f.close()
		print "Results saved in listselection_%s.txt" % selection
		
cmd.extend('listselection',listselection)
