# -*- coding: utf-8  -*-
import re
import requests
import json
import pywikibot
import sys

#parameters to set
lang = 'de'
project = 'wikisource'
template  = 'REDaten'
template2 = 'REAutor'
startWith = 476000 #page id
##################

site = pywikibot.Site('wikidata', 'wikidata')
repo = site.data_repository()
site2 = pywikibot.Site('de', 'wikisource')
site3 = pywikibot.Site('de', 'wikipedia')

authors = {"Karlhans Abel.": "Karlhans Abel", u"Abert.": "Hermann Abert", u"Achelis.": "Hans Achelis", u"Adler.": "Ada Adler", u"P. Ahlert.": "Paulheinz Ahlert", u"Aly.": "Wolfgang Aly", u"W. Aly.": "Wolfgang Aly", u"Wolf Aly.": "Wolfgang Aly", u"Amelung.": "Walter Amelung", u"Andreas.": "Friedrich Carl Andreas", u"Andres.": "Friedrich Andres", u"Arendt †.": "Fritz Arendt", u"v. Arnim.": "Hans von Arnim", u"Assmann.": "Ernst Assmann", u"E. Assmann.": "Ernst Assmann", u"Atenstädt.": "Felix Atenstädt", u"Aust.": "Emil Aust", u"Aulitzky.": "Karl Aulitzky", u"Herbert Bannert.": "Herbert Bannert", u"Luisa Banti.": "Luisa Banti", u"Kurt Bardong.": "Kurt Bardong", u"Barkowski.": "Otto Barkowski", u"F. Baumgarten.": "Fritz Baumgarten", u"Baumgartner.": "Adolf Baumgartner", u"Baumstark.": "Anton Baumstark| junior", u"Beer.": "Georg Beer", u"Jost Benedum.": "Jost Benedum", u"Benjamin.": "Conrad Benjamin", u"Benzinger.": "Immanuel Benzinger", u"Adolf Berger.": "Adolf Berger", u"E. Bernert.": "Ernst Bernert", u"Berger.": "Ernst Hugo Berger", u"Berve.": "Helmut Berve", u"M. Besnier.": "Maurice Besnier", u"Bethe.": "Erich Bethe", u"Bezold.": "Carl Bezold", u"Bidez.": "Joseph Bidez", u"Bigott.": "Edmund Bigott", u"Bilabel.": "Friedrich Bilabel", u"Bischoff.": "Ernst Bischoff", u"v. Bissing.": "Friedrich Wilhelm von Bissing", u"Bitterauf.": "Karl Bitterauf", u"v. Blumenthal.": "Albrecht von Blumenthal", u"A. v. Blumenthal.": "Albrecht von Blumenthal", u"Blümner.": "Hugo Blümner", u"Boehm.": "Fritz Böhm", u"Boerner.": "Adolf Boerner", u"Robert Böker.": "Robert Böker", u"Bölte.": "Felix Bölte", u"F. Bölte.": "Felix Bölte", u"Boll.": "Franz Boll| (Philologe)", u"Mario Bonaria.": "Mario Bonaria", u"Stefan Borzsák.": "István Borzsák", u"St. Borzsák.": "István Borzsák", u"Brandis.": "Karl Georg Brandis", u"S. Brandt.": "Samuel Brandt", u"W. Brandenstein.": "Wilhelm Brandenstein", u"Brassloff.": "Stephan Brassloff", u"Brommer.": "Frank Brommer", u"F. Brommer.": "Frank Brommer", u"Frank Brommer.": "Frank Brommer", u"Brzoska.": "Julius Brzoska", u"Burchardt.": "Max Burchardt| (Ägyptologe)", u"Bürchner.": "Ludwig Bürchner", u"Büttner-Wobst.": "Theodor Büttner-Wobst", u"W. Capelle.": "Wilhelm Capelle", u"Capps.": "Edward Capps", u"D. Cauer.": "Detlef Cauer", u"Cauer.": "Friedrich Cauer", u"F. Cauer.": "Friedrich Cauer", u"Cichorius.": "Conrad Cichorius", u"Carl Joachim Classen.": "Carl Joachim Classen", u"C. Joachim Classen.":  "Carl Joachim Classen", u"C. Clemen.": "Carl Clemen", u"Cohn.": "Leopold Cohn", u"Consbruch.": "Max Consbruch", u"Conradt.": "Karl Conradt", u"Ch. Courtois.": "Christian Courtois", u"Cramer.": "Franz Cramer", u"W. Crönert.": "Wilhelm Crönert", u"Crönert.": "Wilhelm Crönert", u"Crusius.": "Otto Crusius", u"Cumont.": "Franz Cumont", u"Daebritz.": "Rudolf Daebritz", u"Dahms.": "Rudolf Dahms| (1880–1959)", u"Chr. M. Danoff.": "Christo M. Danoff", u"Degering.": "Hermann Degering", u"Jürgen Deininger.": "Jürgen Deininger", u"Alexander Demandt.": "Alexander Demandt", u"Dessau.": "Hermann Dessau", u"de Stefani.": "Eduardo Luigi De Stefani", u"De Stefani.": "Eduardo Luigi De Stefani", u"H.-J. Diesner.": "Hans-Joachim Diesner", u"Diehl.": "Ernst Diehl", u"Erich Diehl.": "Erich Diehl", u"Dieterich.": "Albrecht Dieterich", u"Dittenberger.": "Wilhelm Dittenberger", u"Heinrich Dörrie.": "Heinrich Dörrie", u"v. Domaszewski.": "Alfred von Domaszewski", u"Doyé.": "Karl Daniel Doyé", u"Droysen.": "Hans Droysen", u"Dümmler.": "Ferdinand Dümmler", u"Dumrese.": "Hans Dumrese", u"Dziatzko.": "Karl Dziatzko", u"Ebert.": "Friedrich Ebert| (Historiker)", u"Werner Eck.": "Werner Eck", u"Eitrem.": "Samson Eitrem", u"S. Eitrem.": "Samson Eitrem", u"W. Enßlin.":  "Wilhelm Enßlin", u"Wilh. Enßlin.": "Wilhelm Enßlin", u"Enßlin.":  "Wilhelm Enßlin", u"Escher.": "Jakob Escher-Bürkli", u"Fabricius.": "Ernst Fabricius", u"E. Fabricius.": "Ernst Fabricius", u"Erich Fascher.": "Erich Fascher", u"Fiebiger.": "Otto Fiebiger", u"Fiechter.": "Ernst Robert Fiechter", u"Fiehn.": "Karl Fiehn", u"Fiesel.": "Eva Fiesel", u"E. Fiesel.": "Eva Fiesel", u"Eva Fiesel.": "Eva Fiesel", u"Fimmen.": "Diedrich Fimmen", u"Fischer.": "Curt Theodor Fischer", u"Eitel Fischer.": "Eitel Fischer", u"Jos. Fischer.": "Joseph Fischer| (Geograph)", u"Jenő Fitz.": "Jenő Fitz", u"Jenö Fitz.": "Jenő Fitz", u"Fitzler.": "Kurt Fitzler", u"Max Fluss.": "Max Fluß", u"Fluss.": "Max Fluß", u"Foerster.": "Richard Foerster", u"Fraenkel.": "Siegmund Fraenkel", u"Fränkel.": "Siegmund Fraenkel", u"Franke.": "Alfred Franke", u"Alfred Franke.": "Alfred Franke", u"Alfred Franke †.": "Alfred Franke", u"Frankenstein.": "Lili Frankenstein", u"Fredrich.": "Carl Fredrich", u"Freudenthal.": "Jacob Freudenthal", u"J. Friedrich.": "Johannes Friedrich", u"K. v. Fritz.": "Kurt von Fritz", u"Fröhlich.": "Franz Fröhlich", u"W. Fröhner.": "Wilhelm Fröhner", u"Ferenc Fülep.": "Ferenc Fülep", u"Funaioli.": "Gino Funaioli", u"Gaheis.": "Alexander Gaheis", u"Gall.": "Robert Gall", u"Ganschinietz.": "Richard Ganschinietz", u"Gardthausen.": "Viktor Gardthausen", u"Gärtner.": "Hans Gärtner", u"V. Gebhard.": "Viktor Gebhard", u"Geiger.":  "Friedrich Geiger", u"F. Geiger.": "Friedrich Geiger", u"H. v. Geisau.":  "Hans von Geisau", u"v. Geisau.":  "Hans von Geisau", u"Hans v. Geisau.": "Hans von Geisau", u"J. Geffcken.": "Johannes Geffcken| (Philologe)", u"Geffcken.": "Johannes Geffcken| (Philologe)", u"Gelzer.": "Matthias Gelzer", u"Gensel.": "Paul Gensel", u"G. Gentz.": "Günter Gentz", u"Gercke.": "Alfred Gercke", u"Gerhard.": "Gustav Adolf Gerhard", u"Gerth.": "Karl Gerth", u"Geyer.": "Fritz Geyer| (Historiker)", u"Fritz Geyer.": "Fritz Geyer| (Historiker)", u"Ginzel.": "Friedrich Karl Ginzel", u"F. Gisinger.": "Friedrich Gisinger", u"Konrad Glaser.": "Konrad Glaser", u"P. Goessler.": "Peter Goessler", u"Goetz.": "Georg Goetz", u"Goldfinger.": "Robert Goldfinger", u"Gossen.": "Hans Gossen", u"Hans Gossen.": "Hans Gossen", u"Graef.": "Botho Graef", u"Graf.": "Ernst Graf", u"Graffunder.": "Paul Graffunder", u"Grapow.": "Hermann Grapow", u"Greßmann.": "Hugo Gressmann", u"v. Grienberger.": "Theodor von Grienberger", u"Grimme.": "Hubert Grimme", u"Groag.": "Edmund Groag", u"Groebe.":  "Paul Groebe", u"P. Groebe.": "Paul Groebe", u"Grohmann.":  "Adolf Grohmann", u"Adolf Grohmann.": "Adolf Grohmann", u"W. H. Groß.": "Walter Hatto Gross", u"Robert Grosse.": "Robert Grosse", u"Gruppe.": "Otto Gruppe", u"Gudeman.": "Alfred Gudeman", u"A. Gudeman.": "Alfred Gudeman", u"H. Gundel.": "Hans Georg Gundel", u"Hans Gundel.": "Hans Georg Gundel", u"Gundel.": "Wilhelm Gundel", u"Habel.": "Paul Habel", u"Häbler.": "Albin Haebler", u"Haebler.": "Albin Haebler", u"Hähnle.": "Karl Hähnle", u"Hanslik.": "Rudolf Hanslik", u"Rudolf Hanslik.": "Rudolf Hanslik", u"Hartmann.": "Ludo Moritz Hartmann", u"R. Hartmann.": "Richard Hartmann", u"Haug.": "Ferdinand Haug", u"Haverfield.": "Francis John Haverfield", u"Heckenbach.": "Josef Heckenbach", u"Heibges.": "Stephan Heibges", u"Heichelheim.": "Fritz Moritz Heichelheim", u"Fritz Heichelheim.": "Fritz Moritz Heichelheim", u"I. Heinemann.": "Isaak Heinemann", u"Wolfgang Helck.": "Wolfgang Helck", u"Henze.": "Walter Henze", u"Herbig.": "Gustav Herbig", u"Rudolf Herbst.": "Rudolf Herbst", u"Herrmann.": "Albert Herrmann", u"Albert Herrmann.": "Albert Herrmann", u"Hans Herter.": "Hans Herter", u"Gertrud Herzog-Hauser.": "Gertrud Herzog-Hauser", u"Hill.": "George Francis Hill", u"Hiller v. Gaertringen.": "Friedrich Hiller von Gaertringen", u"Hiller v. Gärtringen.":  "Friedrich Hiller von Gaertringen", u"Hiller von Gaertringen.": "Friedrich Hiller von Gaertringen", u"v. Hiller.": "Friedrich Hiller von Gaertringen", u"Walther Hinz.": "Walther Hinz", u"J. Hirschberg.": "Julius Hirschberg", u"Hirschfeld.": "Gustav Hirschfeld", u"Hitzig.": "Hermann Ferdinand Hitzig", u"Hoefer.": "Ulrich Hoefer", u"W. Hoffmann.": "Wilhelm Hoffmann", u"Hohl.": "Ernst Hohl", u"Hölscher.":  "Gustav Hölscher", u"G. Hölscher.": "Gustav Hölscher", u"Honigmann.":  "Ernst Honigmann", u"E. Honigmann.":  "Ernst Honigmann", u"Ernst Honigmann.": "Ernst Honigmann", u"Hopfner.": "Isidor Hopfner", u"Th. Hopfner.": "Theodor Hopfner", u"Hosius.": "Carl Hosius", u"Hübner.": "Emil Hübner", u"Hülsen.": "Christian Hülsen", u"Hug.": "August Hug", u"Hula.": "Eduard Hula", u"Hultsch.": "Friedrich Hultsch", u"Ihm.": "Maximilian Ihm", u"Imhoof-Blumer.": "Friedrich Imhoof-Blumer", u"F. Jacoby.": "Felix Jacoby", u"Shelagh Jameson.": "Shelagh Jameson", u"v. Jan.": "Karl von Jan", u"Jessen.": "Otto Jessen", u"Jörs.": "Paul Jörs", u"Judeich.": "Walther Judeich", u"Jülicher.": "Adolf Jülicher", u"A. Jülicher.": "Adolf Jülicher", u"Jüthner.": "Julius Jüthner", u"P. J. Junge.": "Peter Julius Junge", u"Kaerst.": "Julius Kaerst", u"Kahrstedt.": "Ulrich Kahrstedt", u"Kaibel.": "Georg Kaibel", u"Kauffmann.": "Georg Kauffmann", u"Kazarow.": "Gawril Kazarow", u"Kappelmacher.": "Alfred Kappelmacher", u"Stefan Karwiese.": "Stefan Karwiese", u"Kees.": "Hermann Kees", u"H. Kees.": "Hermann Kees", u"Herm. Kees.": "Hermann Kees", u"J. Keil.": "Josef Keil", u"Keil.": "Josef Keil", u"O. Keller.": "Otto Keller| (Philologe)", u"Keune.": "Johann Baptist Keune", u"Kern.": "Otto Kern", u"O. Kern.": "Otto Kern", u"E. Kirsten.":  "Ernst Kirsten", u"Ernst Kirsten.": "Ernst Kirsten", u"Kiessling.": "Max Kiessling", u"M. Kießling †.": "Max Kiessling", u"Kind.": "Friedrich Ernst Kind", u"Kipp.": "Theodor Kipp", u"Kirchner.": "Johannes Kirchner", u"Johannes Kirchner.": "Johannes Kirchner", u"Johann Kirchner.": "Johannes Kirchner", u"Klass.": "Justinus Klass", u"Klebs.": "Elimar Klebs", u"Kleinfeller.": "Georg Kleinfeller", u"Klek.": "Joseph Klek", u"Kletzel.": "Wolfgang Kletzel", u"Klingmüller.": "Fritz Klingmüller", u"Klotz.": "Alfred Klotz", u"Knaack.": "Georg Knaack", u"Koch.": "Emil Koch", u"Kock.": "Bernhard Kock", u"Alfred Körte.": "Alfred Körte", u"A. Körte.":  "Alfred Körte", u"Körte.":  "Alfred Körte", u"Kolbe.": "Walther Kolbe", u"Marie C. van der Kolf.": "Marie Christina van der Kolf", u"M. C. van der Kolf.": "Marie Christina van der Kolf", u"Kornemann.": "Ernst Kornemann", u"Ernst Kornemann.": "Ernst Kornemann", u"H. Kortenbeutel.": "Heinz Kortenbeutel", u"v. Kotz-Dobrž.": "Wolfgang von Kotz-Dobrž", u"E. Krämer.": "Ernst Krämer", u"M. Krause.": "Max Krause| (Arabist)", u"Krauss.": "Samuel Krauss", u"K. Kretschmer.": "Konrad Kretschmer", u"E. Kriaras.": "Emmanuel Kriaras", u"Kroll.": "Wilhelm Kroll", u"W. Kroll.": "Wilhelm Kroll", u"Kröner.": "Hans-Otto Kröner", u"H.-O. Kröner.": "Hans-Otto Kröner", u"O. Krückmann.": "Oluf Krückmann", u"Kruse.": "Bernhard große Kruse", u"gr. Kruse.": "Bernhard große Kruse", u"Kubitschek.": "Wilhelm Kubitschek", u"Wilh. Kubitschek.": "Wilhelm Kubitschek", u"W. Kubitschek †.": "Wilhelm Kubitschek", u"Fridolf Kudlien.": "Fridolf Kudlien", u"Kübler.": "Bernhard Kübler", u"B. Kübler.": "Bernhard Kübler", u"P. Kübler.": "Paul Kübler", u"Lackeit.": "Conrad Lackeit", u"Lagercrantz.": "Otto Lagercrantz", u"Lambertz.": "Maximilian Lambertz", u"Lamer.": "Hans Lamer", u"H. Lamer.": "Hans Lamer", u"Lammert.": "Edmund Lammert", u"E. Lammert.": "Edmund Lammert", u"Friedrich Lammert.": "Friedrich Lammert", u"Richard Laqueur.": "Richard Laqueur", u"Kurt Latte.": "Kurt Latte", u"Laum.": "Bernhard Laum", u"Leist.": "Gerhard Alexander Leist", u"G. A. Leist.": "Gerhard Alexander Leist", u"Lenschau.": "Thomas Lenschau", u"Th. Lenschau.": "Thomas Lenschau", u"Thomas Lenschau.": "Thomas Lenschau", u"Leonhard.": "Rudolf Leonhard| (Jurist)", u"R. Leonhard.": "Rudolf Leonhard| (Jurist)", u"Lieben.": "Eugen Lieben", u"Liebenam.": "Wilhelm Liebenam", u"Lietzmann.": "Hans Lietzmann", u"E. Linckenheld.": "Emil Linckenheld", u"Adolf Lippold.": "Adolf Lippold", u"Lippold.": "Georg Lippold", u"G. Lippold.": "Georg Lippold", u"Georg Lippold.": "Georg Lippold", u"E. Littmann.": "Enno Littmann", u"Gerhard Loeschcke.": "Gerhard Loeschcke", u"Loeschcke.": "Georg Loeschcke", u"Walther Ludwig.": "Walther Ludwig", u"Luebeck.": "Emil Luebeck", u"R. Lullies.": "Reinhard Lullies", u"Macdonald.": "George MacDonald| (Numismatiker)", u"G. Macdonald.": "George MacDonald| (Numismatiker)", u"Manigk.": "Alfred Manigk", u"Marbach.": "Ernst Marbach", u"E. Marbach.": "Ernst Marbach", u"Ernst Marbach.": "Ernst Marbach", u"Ernst Marbach. †": "Ernst Marbach", u"M. Marcovich.": "Miroslav Marcovich", u"Sc. Mariotti.": "Scevola Mariotti", u"Martin.": "Josef Martin", u"Martini.": "Edgar Martini", u"A. Marx.": "August Marx", u"F. Marx.": "Friedrich Marx| (Philologe)", u"Mau.": "August Mau", u"Maximilian Mayer.": "Maximilian Mayer", u"P. J. Meier.": "Paul Jonas Meier", u"Ed. Meyer.": "Eduard Meyer", u"E. Meyer.": "Eduard Meyer", u"Ernst Meyer.": "Ernst Meyer| (Historiker)", u"Markwart Michler.": "Markwart Michler", u"G. Mickwitz.": "Gunnar Mickwitz", u"Mielentz.": "Fritz Mielentz", u"Milchhöfer.": "Arthur Milchhöfer", u"Milchhoefer.": "Arthur Milchhöfer", u"J. Miller.": "Julius Miller", u"Fr. Miltner.": "Franz Miltner", u"F. Miltner.": "Franz Miltner", u"Miltner.": "Franz Miltner", u"Andreas Mócsy.": "András Mócsy", u"Anneliese Modrze.": "Annelise Modrze", u"Annelise Modrze.": "Annelise Modrze", u"Moritz.": "Bernhard Moritz", u"B. A. Müller.": "Bruno Albin Müller", u"D. H. Müller.": "David Heinrich von Müller", u"K. K. Müller.": "Karl Konrad Müller", u"Konrad Müller.": "Konrad Müller", u"Lothar Müller.": "Lothar Müller", u"Münscher.": "Karl Münscher", u"Münzel.": "Robert Münzel", u"Münzer.": "Friedrich Münzer", u"F. Münzer.": "Friedrich Münzer", u"Natorp.": "Paul Natorp", u"Nagl.": "Maria Assunta Nagl", u"A. Nagl.": "Alfred Nagl", u"Alf. Nagl.": "Alfred Nagl", u"Alfr. Nagl.": "Alfred Nagl", u"Assunta Nagl.": "Maria Assunta Nagl", u"L. Nagy.":  "Lajos Nagy", u"Nawrath.": "Alfred Nawrath", u"A. R. Neumann.": "Alfred Richard Neumann", u"Neumann.": "Karl Johannes Neumann", u"Nies.": "August Nies", u"Niese.": "Benedikt Niese", u"Nöldeke.": "Theodor Nöldeke", u"Oberhummer.": "Eugen Oberhummer", u"E. Oberhummer.": "Eugen Oberhummer", u"Eugen Oberhummer.": "Eugen Oberhummer", u"Obst.": "Ernst Obst", u"Oder.": "Eugen Oder", u"Oehler.": "Johann Oehler", u"J. Oehler.": "Johann Oehler", u"R. Oehler.": "Raimund Oehler", u"Olck.": "Franz Olck", u"Oldfather.": "William Abbott Oldfather", u"Wm. A. Oldfather.": "William Abbott Oldfather", u"Lotte Ollendorff.": "Charlotte Ollendorff", u"Eckart Olshausen.": "Eckart Olshausen", u"Opitz.": "Hans-Georg Opitz", u"H. G. Opitz.": "Hans-Georg Opitz", u"H.-G. Opitz.": "Hans-Georg Opitz", u"Oppermann.":  "Hans Oppermann", u"Hans Oppermann.": "Hans Oppermann", u"K. Orinsky.": "Kurt Orinsky", u"Orth.": "Ferdinand Orth", u"Ostern.": "Hermann Ostern", u"Walter Otto.": "Walter Otto", u"Otto.":  "Walter F. Otto", u"W. F. Otto.": "Walter F. Otto", u"Oxé.": "August Oxé", u"J. Papastavrou.": "Johannes Papastavrou", u"Johannes Papastavrou.": "Johannes Papastavrou", u"Partsch.": "Joseph Partsch", u"Patsch.": "Carl Patsch", u"W. Peek.": "Werner Peek", u"v. Petrikovits.": "Harald von Petrikovits", u"Pfaff.": "Ivo Pfaff", u"Pfuhl.": "Ernst Pfuhl", u"Philipp.": "Hans Philipp| (Geograph)", u"Hans Philipp.": "Hans Philipp| (Geograph)", u"Philippson.": "Alfred Philippson", u"Pieper.": "Max Pieper", u"M. Pieper.": "Max Pieper", u"Pieske.": "Erich Pieske", u"Pietschmann.": "Richard Pietschmann", u"Plasberg.": "Otto Plasberg", u"Plaumann.": "Gerhard Plaumann", u"M. Plessner.": "Martin Plessner", u"Eckhard Plümacher.": "Eckhard Plümacher", u"Poland.": "Franz Poland", u"F. Poland.": "Franz Poland", u"Pollack.": "Erwin Pollack", u"Pollak.": "Erwin Pollack", u"Pomtow.": "Hans Pomtow", u"Praechter.": "Karl Praechter", u"K. Praechter.": "Karl Praechter", u"Karl Preisendanz.": "Karl Preisendanz", u"Prehn.": "Bruno Prehn", u"Preisigke.": "Friedrich Preisigke", u"A. v. Premerstein.": "Anton von Premerstein", u"v. Premerstein.":  "Anton von Premerstein", u"Preuner.": "Erich Preuner", u"Puchstein.": "Otto Puchstein", u"Radermacher.": "Ludwig Radermacher", u"v. Radinger.": "Karl Radinger von Radinghofen", u"G. Radke.":  "Gerhard Radke", u"Gerhard Radke.": "Gerhard Radke", u"Rappaport.": "Bruno Rappaport", u"Rau.": "Reinhold Rau", u"Regling.": "Kurt Regling", u"K. Regling.": "Kurt Regling", u"Rehm.": "Albert Rehm", u"Reisch.": "Emil Reisch", u"Reitzenstein.": "Richard Reitzenstein", u"R. Reitzenstein.": "Richard Reitzenstein", u"Riba.": "Maximilian Riba", u"Richter.": "Franz Richter| (Altphilologe)", u"H. Riemann.": "Hans Riemann", u"W. Riemschneider.": "Wilhelm Riemschneider", u"Wilhelm Riemschneider.": "Wilhelm Riemschneider", u"Riess.": "Ernst Riess", u"Fr. Rietzsch.": "Franz Rietzsch", u"C. Robert.": "Carl Robert", u"Rodenwaldt.": "Gerhart Rodenwaldt", u"v. Rohden.": "Paul von Rohden", u"P. v. Rohden.": "Paul von Rohden", u"P. v. Rhoden.": "Paul von Rohden", u"Rosenberg.": "Arthur Rosenberg", u"O. Rossbach.": "Otto Rossbach", u"Rostowzew.": "Michael Rostovtzeff", u"Rothansel.": "Ludwig Rothansel", u"Ruge.": "Walther Ruge", u"W. Ruge.": "Walther Ruge", u"Andreas Rumpf.": "Andreas Rumpf", u"Rzach.": "Alois Rzach", u"E. Sachers.": "Erich Sachers", u"Sakolowski.": "Paul Sakolowski", u"Samter.": "Ernst Samter", u"B. Saria.": "Balduin Saria", u"Jaroslav Šašel.": "Jaroslav Šašel", u"Sauer.": "Bruno Sauer", u"Hans Schaefer.": "Hans Schaefer", u"Schaefer.": "Heinrich Wilhelm Schaefer", u"Schenk.": "Arno Schenk", u"Scherling.":  "Karl Scherling", u"K. Scherling.": "Karl Scherling", u"Karl Scherling.": "Karl Scherling", u"Schiff.": "Alfred Schiff", u"Schissel.": "Otmar Schissel von Fleschenberg", u"Schmekel.": "August Schmekel", u"Schmid.": "Wilhelm Schmid", u"W. Schmid.": "Wilhelm Schmid", u"Johanna Schmidt.": "Johanna Schmidt", u"J. Schmidt.": "Johannes Schmidt (Epigraphiker)", u"Joh. Schmidt.": "Johannes Schmidt (Epigraphiker)", u"L. Schmidt.": "Leopold Schmidt", u"Ludw. Schmidt.": "Ludwig Schmidt| (Historiker)", u"M. C. P. Schmidt.": "Max C. P. Schmidt", u"Max C. P. Schmidt.": "Max C. P. Schmidt", u"K. Schneider.": "Karl Schneider", u"Schoch.": "Paul Schoch", u"v. Schoeffer.": "Valerian von Schoeffer", u"v. Schöffer.":  "Valerian von Schoeffer", u"Schönfeld.":  "Moritz Schönfeld", u"A. Schramm.": "Albert Schramm", u"Wilt Aden Schröder.": "Wilt Aden Schröder", u"Schroff.": "Helmut Schroff", u"Schulten.":  "Adolf Schulten", u"A. Schulten.":  "Adolf Schulten", u"Ad. Schulten.": "Adolf Schulten", u"Schulthess.": "Otto Schulthess", u"Schultheß.": "Otto Schulthess", u"Otto Schultheß.": "Otto Schulthess", u"H. Schultz.": "Hermann Schultz| (Philologe)", u"Schultz.": "Hermann Schultz| (Philologe)", u"W. Schultz.": "Wolfgang Schultz", u"Schultz.": "Wolfgang Schultz", u"Schwabe. †": "Ernst Schwabe", u"Schwabe †.": "Ernst Schwabe", u"Schwabe.†": "Ernst Schwabe", u"Schwabe.": "Ernst Schwabe", u"Schwahn.": "Walther Schwahn", u"Schwartz.": "Eduard Schwartz", u"E. Schwyzer.": "Eduard Schwyzer", u"Seeck.": "Otto Seeck", u"Sethe.": "Kurt Sethe", u"Sickenberger.": "Joseph Sickenberger", u"J. Sieveking.": "Johannes Sieveking", u"Sittig.": "Ernst Sittig", u"Sitzler.": "Jakob Sitzler", u"Skutsch.": "Franz Skutsch", u"Walther Sontheimer.": "Walther Sontheimer", u"Stadler.": "Hermann Stadler", u"Stähelin.": "Felix Stähelin", u"F. Staehelin.": "Felix Stähelin", u"Felix Stähelin.": "Felix Stähelin", u"Stählin.": "Friedrich Stählin", u"F. Stählin.": "Friedrich Stählin", u"Friedr. Stählin.": "Friedrich Stählin", u"Friedrich Stählin.": "Friedrich Stählin", u"Stech.": "Bruno Stech", u"Stegemann.":  "Willy Stegemann", u"Willy Stegemann.": "Willy Stegemann", u"Steier.": "August Steier", u"Stein.": "Arthur Stein", u"O. Stein.": "Otto Stein", u"Steiner.": "Alfons Steiner", u"Stöckle.": "Albert Stöckle", u"F. Stoessl.": "Franz Stoessl", u"Franz Stoessl.": "Franz Stoessl", u"Stengel.": "Paul Stengel", u"Stenzel.": "Julius Stenzel", u"Streck.": "Maximilian Streck", u"J. Sturm.": "Josef Sturm", u"Sundwall.": "Johannes Sundwall", u"E. Swoboda.": "Erich Swoboda", u"Swoboda.": "Heinrich Swoboda| (Althistoriker)", u"Sykutris.": "Ioannis Sykutris", u"Samuel Szádeczky-Kardoss.": "Samu Szádeczky-Kardoss", u"Szanto.": "Emil Szanto", u"Tambornino.": "Julius Tambornino", u"Thalheim.": "Theodor Thalheim", u"Thiele.": "Georg Thiele", u"Bengt E. Thomasson.": "Bengt E. Thomasson", u"Thrämer.": "Eduard Thraemer", u"Thraemer.": "Eduard Thraemer", u"Thulin.": "Carl Thulin", u"Tittel.": "Karl Tittel", u"Tkač.": "Jaroslav Tkáč", u"Toepffer.": "Johannes Toepffer", u"Tolkiehn.": "Johannes Tolkiehn", u"Tomaschek.":  "Wilhelm Tomaschek", u"Tomaschek †.":  "Wilhelm Tomaschek", u"W. Tomaschek.": "Wilhelm Tomaschek", u"Tomascheck.":  "Wilhelm Tomaschek", u"Treidler.": "Hans Treidler", u"Hans Treidler.": "Hans Treidler", u"Max Treu.": "Max Treu", u"Mary L. Trowbridge.": "Mary Luella Trowbridge", u"Tümpel.": "Karl Tümpel", u"Türk.": "Gustav Türk", u"G. Türk.": "Gustav Türk", u"W. v. Uxkull.": "Woldemar Graf Uxkull-Gyllenband", u"A. W. Van Buren.": "Albert William Van Buren", u"Vetter.":  "Emil Vetter", u"E. Vetter.": "Emil Vetter", u"Viedebantt.":  "Oskar Viedebantt", u"Hans Volkmann.": "Hans Volkmann", u"Vollmer.": "Friedrich Vollmer", u"Vonder Mühll.": "Friedrich von der Mühll", u"Vulić.": "Nikola Vulić", u"Wachsmuth.": "Kurt Wachsmuth", u"Wagler.": "Paul Wagler", u"Wagner.": "Richard Wagner| (Philologe)", u"Wolfgang Waldstein.": "Wolfgang Waldstein", u"Hans Walter.": "Hans Walter", u"Waser.": "Otto Waser", u"Wecker.": "Otto Wecker", u"Weidlich.": "Theodor Weidlich", u"Richard D. Weigel.": "Richard D. Weigel", u"Weinberger.": "Wilhelm Weinberger", u"Weinel.": "Heinrich Weinel", u"Weinstock.": "Stefan Weinstock", u"St. Weinstock.": "Stefan Weinstock", u"Weiss.": "Jakob Weiss", u"Weissbach.":  "Franz Heinrich Weißbach", u"Weißbach.":  "Franz Heinrich Weißbach", u"F. H. Weissbach.": "Franz Heinrich Weißbach", u"E. Wellmann.": "Eduard Wellmann", u"M. Wellmann.": "Max Wellmann", u"Wendling.": "Emil Wendling", u"Wentzel.": "Georg Wentzel", u"Wernicke.": "Konrad Wernicke", u"Wessner.": "Paul Wessner", u"Weynand.": "Rudolf Weynand", u"Hans Widmann.": "Hans Widmann", u"Wiedersich.": "Alfons Wiedersich", u"Wiegand.": "Theodor Wiegand", u"Wilcken.": "Ulrich Wilcken", u"U. Wilcken.": "Ulrich Wilcken", u"Wilhelm.": "Adolf Wilhelm", u"Williger.": "Eduard Williger", u"Willrich.": "Hugo Willrich", u"F. Windberg.": "Friedrich Windberg", u"Gerhard Winkler.": "Gerhard Winkler", u"Wissowa.": "Georg Wissowa", u"Georg Wissowa.": "Georg Wissowa", u"Witte.": "Kurt Witte", u"Wlassak.": "Moriz Wlassak", u"M. Wlassak.": "Moriz Wlassak", u"Wolff.": "Alfred Wolff", u"v. Wotawa.": "August von Wotawa", u"F. Wotke.": "Friedrich Wotke", u"Friedrich Wotke.": "Friedrich Wotke", u"Wünsch.": "Richard Wünsch", u"Ernst Wüst.": "Ernst Wüst", u"Zeiß.": "Hans Zeiss", u"Zeiss.": "Hans Zeiss", u"Zeuss.": "Hans Zeiss", u"Zahn.": "Robert Zahn", u"Ziebarth.": "Erich Ziebarth", u"E. Ziebarth.": "Erich Ziebarth", u"Erich Ziebarth.": "Erich Ziebarth", u"Ziegler.": "Konrat Ziegler", u"Konrat Ziegler.": "Konrat Ziegler", u"Ziehen.":  "Ludwig Ziehen", u"Ludwig Ziehen.": "Ludwig Ziehen", u"Zieseniss.": "Alexander Zieseniss", u"Zschietzschmann.":  "Willy Zschietzschmann", u"Willy Zschietzschmann.": "Willy Zschietzschmann", u"Zwicker.": "Johannes Zwicker"}

def createItem():
    payload = {
        'language': 'de',
        'project': 'wikisource',
        'categories': 'Paulys Realencyclopädie der classischen Altertumswissenschaft',
        'negcats': 'RE:Verweisung',
        'ns[0]': '1',
        'show_redirects': 'no',
        'wikidata_item': 'without',
        'doit': '1',
        'format': 'json'
    }
    r = requests.get('http://petscan.wmflabs.org/', params=payload)
    data = r.json()
    for m in data['*'][0]['a']['*']:
        sitelink = m['title'].replace('_', ' ')
        if sitelink[0:3] != 'RE:':
            continue
        label = sitelink[3:] + ' (Pauly-Wissowa)'
        data = {'sitelinks': {'dewikisource': {'site': 'dewikisource', 'title': sitelink}} , 'labels':{'de':{'language':'de','value': label}, 'en':{'language':'en','value': label}}, 'descriptions':{'de':{'language':'de','value': 'Artikel in Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)'}, 'en':{'language':'en','value': 'article in Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)'}}}
        newitem = pywikibot.ItemPage(repo)
        newitem.editEntity(data=data)
        addClaims(sitelink)

    payload = {
        'language': 'de',
        'project': 'wikisource',
        'categories': 'RE:Verweisung',
        'ns[0]': '1',
        'show_redirects': 'no',
        'wikidata_item': 'without',
        'doit': '1',
        'format': 'json'
    }
    r = requests.get('http://petscan.wmflabs.org/', params=payload)
    data = r.json()
    for m in data['*'][0]['a']['*']:
        sitelink = m['title'].replace('_', ' ')
        if not iscrossreference(sitelink):
            continue
        if sitelink[0:3] != 'RE:':
            continue
        label = sitelink[3:] + ' (Pauly-Wissowa)'
        data = {'sitelinks': {'dewikisource': {'site': 'dewikisource', 'title': sitelink}}, 'labels':{'de':{'language':'de','value': label}, 'en':{'language':'en','value': label}}, 'descriptions':{'de':{'language':'de','value': 'Verweisung in Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)'}, 'en':{'language':'en','value': 'cross-reference in Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)'}}}
        newitem = pywikibot.ItemPage(repo)
        newitem.editEntity(data=data)
        addClaims(sitelink)


def iscrossreference(sitelink):
    page = pywikibot.Page(site2, sitelink)
    if len(page.get()) < 500:    
        for cat in page.categories():
            if 'Kategorie:RE:Verweisung' in cat.title():
                return True
    return False
        
def parseTemplate(text, templateName, parameterName):
    open = 1
    save = 0
    result = ''
    foo = text.split(u'{{'+templateName)
    if len(foo) == 1:
        foo = text.split(u'{{'+templateName.lower())
    if len(foo) == 1:
        return ''
    parts = re.split(u'(\{\{|\}\}|\||\=|\[\[|\]\])',foo[1]);
    for m in parts[1:]:
        m = m.strip()
        if save == 1  and open == 1 and m == '|': break #end of value
        if m == '{{' or m == '[[': open += 1 #one template deeper
        elif m == '}}' or m == ']]': open -= 1 #one template higher
        if open == 0: break #end of template
        if save == 1: result += m.strip()
        if open == 1 and m.lower() == parameterName.lower(): save = 1 #found paramter on the right level
    if len(result) == 0:
        return ''
    return result[1:]


def parseTemplateNum(text, templateName, parameterNum):
    foo = text.split(u'{{'+templateName)
    if len(foo) != 2:
        foo = text.split(u'{{'+templateName.lower())
    if len(foo) != 2:
        return ''
    parts = re.split(u'(\{\{|\}\}|\||\=|\[\[|\]\])', foo[1]);
    cnt = 0
    for m in parts[2:]:
        if m == '}}':
            break    
        cnt += 1
        if parameterNum == cnt:
            return m.strip()
    return ''

def addClaims(pagetitle):
    page = pywikibot.Page(site2, pagetitle)
    try:
        item = pywikibot.ItemPage.fromPage(page)
    except:
        return 0
    if not item.exists():
        return 0
    if item.isRedirectPage():
        return 0
    text = page.get().replace('\n', '')
    publishedin = parseTemplate(text, template, 'BAND')
    if publishedin == '':
        publishedin = parseTemplate(text, template, 'BD')
    columnstart = parseTemplate(text, template, 'SPALTE_START')
    if columnstart == '':
        columnstart = parseTemplate(text, template, 'SS')
    columnend = parseTemplate(text, template, 'SPALTE_END')
    if columnend == '':
        columnend = parseTemplate(text, template, 'SE')
    prev = parseTemplate(text, template, 'VORGÄNGER')
    if prev == '':
        prev = parseTemplate(text, template, 'VG')
    next = parseTemplate(text, template, 'NACHFOLGER')
    if next == '':
        next = parseTemplate(text, template, 'NF')
    wikipedia = parseTemplate(text, template, 'WIKIPEDIA')
    if wikipedia == '':
        wikipedia = parseTemplate(text, template, 'WP')
    wikisource = parseTemplate(text, template, 'WIKISOURCE')
    if wikisource == '':
        wikisource = parseTemplate(text, template, 'WS')
    author = parseTemplateNum(text, template2, 1)
    author2 = parseTemplateNum(text, template2, 2)

    item.get()

    if 'P31' not in item.claims:
        claim = pywikibot.Claim(repo, 'P31')
        if iscrossreference(pagetitle):
            target= pywikibot.ItemPage(repo, 'Q1302249')
        else:
            target= pywikibot.ItemPage(repo, 'Q13433827')
        claim.setTarget(target)
        item.addClaim(claim)

    if 'P361' not in item.claims:
        claim = pywikibot.Claim(repo, 'P361')
        target= pywikibot.ItemPage(repo, 'Q1138524')
        claim.setTarget(target)
        item.addClaim(claim)

    if 'P1433' in item.claims and publishedin != '':
        if item.claims['P1433'][0].getTarget().getID() == 'Q1138524':
            try:
                claim = item.claims['P1433'][0]
                page1 = pywikibot.Page(site2, 'Kategorie:RE:Band_'+publishedin)
                target = pywikibot.ItemPage.fromPage(page1)
                target.get()
                if 'P577' in target.claims:
                    publishdate = target.claims['P577'][0].getTarget()
                claim.changeTarget(target)
            except:
                pass
    elif 'P1433' not in item.claims and publishedin != '':
        try:
            claim = pywikibot.Claim(repo, 'P1433')
            page1 = pywikibot.Page(site2, 'Kategorie:RE:Band_'+publishedin)
            target = pywikibot.ItemPage.fromPage(page1)
            target.get()
            if 'P577' in target.claims:
                publishdate = target.claims['P577'][0].getTarget()
            claim.setTarget(target)
            item.addClaim(claim)
        except:
            pass

    if 'P577' not in item.claims and 'publishdate' in locals():
        claim = pywikibot.Claim(repo, 'P577')
        claim.setTarget(publishdate)
        item.addClaim(claim)

    if 'P3903' not in item.claims and 'P304' not in item.claims and columnstart != '':
        column = columnstart
        if columnend != '' and columnend != 'OFF':
            column += u'–'+columnend
        claim = pywikibot.Claim(repo, 'P3903')
        claim.setTarget(column)
        item.addClaim(claim)


    if 'P155' not in item.claims and prev != '':
        try:
            claim = pywikibot.Claim(repo, 'P155')
            page1 = pywikibot.Page(site2, 'RE:'+prev)
            target = pywikibot.ItemPage.fromPage(page1)
            claim.setTarget(target)
            item.addClaim(claim)
        except:
            pass

    if 'P156' not in item.claims and next != '':
        try:
            claim = pywikibot.Claim(repo, 'P156')
            page1 = pywikibot.Page(site2, 'RE:'+next)
            target = pywikibot.ItemPage.fromPage(page1)
            claim.setTarget(target)
            item.addClaim(claim)
        except:
            pass

    if 'P921' not in item.claims:
        target = False
        try:
            if wikisource and not wikipedia:
                page1 = pywikibot.Page(site2, wikisource)
                target = pywikibot.ItemPage.fromPage(page1)
            elif wikipedia and not wikisource:
                page1 = pywikibot.Page(site3, wikipedia)
                target = pywikibot.ItemPage.fromPage(page1)
            elif wikipedia and wikisource:
                page1 = pywikibot.Page(site2, wikisource)
                target = pywikibot.ItemPage.fromPage(page1)
                page2 = pywikibot.Page(site3, wikipedia)
                target2 = pywikibot.ItemPage.fromPage(page2)
                if target != target2:
                    target = False
            if target:
                claim = pywikibot.Claim(repo, 'P921')
                claim.setTarget(target)
                item.addClaim(claim)
        except:
            pass

    if 'P50' not in item.claims and author != '':
        if author2 == '':
            if author in authors:
                try:
                    page1 = pywikibot.Page(site2, authors[author].decode('utf-8'))
                    target = pywikibot.ItemPage.fromPage(page1)
                    claim = pywikibot.Claim(repo, 'P50')
                    claim.setTarget(target)
                    item.addClaim(claim)
                except:
                    pass


    terms = {'labels': {}, 'descriptions': {}}
    if page.title()[0:3] != 'RE:':
        return 0
    title = page.title()[3:]
    if 'en' not in item.labels:
        terms['labels']['en'] = {'language': 'en', 'value': title+' (Pauly-Wissowa)'}
    if 'de' not in item.labels:
        terms['labels']['de'] = {'language': 'de', 'value': title+' (Pauly-Wissowa)'}
    elif 'RE:' in item.labels['de'][0:3]:
        terms['labels']['de'] = {'language': 'de', 'value': title+' (Pauly-Wissowa)'}
    if 'en' not in item.descriptions:
        if iscrossreference(pagetitle):
            terms['descriptions']['en'] = {'language': 'en', 'value': 'cross-reference in Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)'}            
        else:
            terms['descriptions']['en'] = {'language': 'en', 'value': 'article in Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)'}        
    if 'de' not in item.descriptions:
        if iscrossreference(pagetitle):
            terms['descriptions']['de'] = {'language': 'de', 'value': 'Verweisung in Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)'}
        else:
            terms['descriptions']['de'] = {'language': 'de', 'value': 'Artikel in Paulys Realencyclopädie der classischen Altertumswissenschaft (RE)'}
    item.editEntity(terms, summary=u' edit terms')


def updateItem():
    atcontinue = template.replace(' ','_')+'|'+str(startWith)
    while True:
        url = 'http://'+lang+'.'+project+'.org/w/api.php?action=query&list=alltransclusions&atprefix=+'+template+'&atprop=ids&atlimit=40&format=json&atcontinue='+str(atcontinue)+'&rawcontinue='
        r = requests.get(url)
        data = r.json()
        pageids = ''
        for m in data['query']['alltransclusions']:
            pageids += str(m['fromid'])+'|'
        url2 = 'https://'+lang+'.'+project+'.org/w/api.php?action=query&pageids='+pageids+'&prop=info&format=json&rawcontinue='
        r2 = requests.get(url2)
        data2 = r2.json()
        for pageid in data2.get('query', {}).get('pages', {}):
            if 'ns' in data2['query']['pages'][pageid]:
                if data2['query']['pages'][pageid]['ns'] == 0:
                    addClaims(data2['query']['pages'][pageid]['title'])
        if 'query-continue' in data:
            atcontinue = data['query-continue']['alltransclusions']['atcontinue']
        else:
            break

if __name__ == "__main__":
    createItem()
    updateItem()

