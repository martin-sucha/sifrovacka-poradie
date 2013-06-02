#!/usr/bin/env python
# coding=UTF-8
import re
import cairo
import pango
import pangocairo
import argparse

argparser = argparse.ArgumentParser()
argparser.add_argument('--iba-casy', action='store_true',
  help='Casy davajme presne (schova niektore popisky)')
argparser.add_argument('subor', help='Vystupny SVG subor')

args = argparser.parse_args()

RE_TIM = re.compile('\<div\>(.*)\</div\>')
RE_CAS = re.compile('\<span\>(.*)\</span\>')

def nacitaj_poradie(subor):
  for line in subor:
    m_tim = RE_TIM.search(line)
    if m_tim:
      tim = m_tim.group(1)
    else:
      m_cas = RE_CAS.search(line)
      if m_cas:
        cas = m_cas.group(1)
        yield tim, cas

def nacitaj_vsetky():
  r = []
  for i in range(1,18):
    with open('{:02d}.html'.format(i), 'rb') as subor:
      r.append(list(nacitaj_poradie(subor)))
  return r

def cas2cislo(cas):
  th, tm = cas.split(':')
  return int(th) * 60 + int(tm) - 9 * 60

stanovistia = nacitaj_vsetky()
vsetky_timy = set()
max_cas = 0
start_cas = cas2cislo('9:00')
koniec_cas = cas2cislo('21:00')

for stanoviste in stanovistia:
  for tim, cas in stanoviste:
    vsetky_timy.update(tim)
    max_cas = max(max_cas, cas2cislo(cas))

vyska_riadku = 20
sirka_stlpca = 440
sirka_ciar = 80
vyska_za_minutu = 10

sirka_obrazka = len(stanovistia) * sirka_stlpca
vyska_obrazka = (vyska_riadku + 
  max((max(koniec_cas, max_cas) - start_cas) * vyska_za_minutu + vyska_riadku,
  vyska_riadku * len(vsetky_timy)))

image = cairo.SVGSurface(args.subor, sirka_obrazka, vyska_obrazka)
context = cairo.Context(image)
context_pc = pangocairo.CairoContext(context)
font = pango.FontDescription('sans 10')

def pis_text(text):
  layout = context_pc.create_layout()
  layout.set_font_description(font)
  layout.set_text(text)
  context.set_source_rgb(0, 0, 0)
  context_pc.update_layout(layout)
  context_pc.show_layout(layout)

for i in range(1,18):
  xpos = (i - 1) * sirka_stlpca
  context.save()
  context.translate(xpos, vyska_riadku)
  pis_text('{}'.format(i) if i < 17 else 'Cieľ')
  context.restore()

xpos = 0
pozicie = None
for stanoviste in stanovistia:
  ypos = vyska_riadku
  minule_pozicie = pozicie
  pozicie = {}
  for poradie, zaznam in enumerate(stanoviste):
    tim, cas = zaznam
    ypos = max(ypos, cas2cislo(cas) * vyska_za_minutu)
    pozicie[tim] = ypos
    
    def vypis_popisok():
      context.save()
      context.translate(xpos, ypos)
      pis_text('{}. {} ({})'.format(poradie + 1, tim, cas))
      context.restore()
    
    if args.iba_casy:
      if poradie + 1 >= len(stanoviste):
        vypis_popisok()
      else:
        dalsi_tim, dalsi_cas = stanoviste[poradie + 1]
        dalsia_ypos = cas2cislo(dalsi_cas) * vyska_za_minutu
        if ypos + vyska_riadku <= dalsia_ypos:
          vypis_popisok()
    else:
      vypis_popisok()
    
    #nakreslime ciary
    context.save()
    context.set_source_rgb(0.5, 0.5, 0.5)
    context.move_to(xpos, ypos)
    context.line_to(xpos + sirka_stlpca - sirka_ciar, ypos)
    context.stroke()
    if minule_pozicie != None and tim in minule_pozicie:
      context.move_to(xpos - sirka_ciar, minule_pozicie[tim])
      context.line_to(xpos, ypos)
      context.stroke()
    context.restore()
    if not args.iba_casy:
      ypos += vyska_riadku
  xpos += sirka_stlpca