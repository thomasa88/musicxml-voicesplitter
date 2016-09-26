#!/usr/bin/python3

import copy
import os.path
import sys
import xml.etree.ElementTree as ET

step_rank = "CDEFGAB"

def note_rank(note):
    pitch = note.find('pitch')
    if pitch is None:
        return None
    octave = int(pitch.find('octave').text) * 7
    step = step_rank.index(pitch.find('step').text)
    alter = pitch.find('alter')
    if alter is None:
        alter = 0
    else:
        alter = int(alter.text) * 0.5
    return octave + step + alter

# def note_cmp(lhs, rhs):
#     l_rank = get_octave_step(lhs)
#     r_rank = get_octave_step(rhs)
#     if l_rank < r_rank:
#         return -1
#     elif l_rank > r_rank:
#         return 1
#     else:
#         return 0

#b1_prev_rank = 99999.0
#b2_prev_rank = 0.0


def one_voice(part, keep):
    prev_highest_voice = 1    
    measures = part.getchildren()
    for measure in measures:
        remove_voice_tags = False
        remove_chord_tags = False
        assert measure.tag == 'measure', 'Assuming only <measure> tags inside <part>'
        print(measure.attrib['number'])
        notes = measure.findall('note')
        found_voices = []
        prev_note = None
        for note in notes:
            voice_elem = note.find('voice')
            voice = voice_elem.text
            if voice not in found_voices:
                #print("found voice", voice)
                found_voices.append(voice)
                if len(found_voices) > 1:
                    # At least two voices in measure
                    remove_voice_tags = True
                    #Maybe chord and voice is combined, so don't break
#            for c in note:
#                print(
            chord = note.find('chord')
            if chord is not None:
                remove_chord_tags = True

                prev_note_rank = note_rank(prev_note)
                current_note_rank = note_rank(note)

                if current_note_rank > prev_note_rank:
                    if keep == prev_highest_voice:
                        measure.remove(prev_note)
                    else:
                        measure.remove(note)
                else:
                    if keep == prev_highest_voice:
                        measure.remove(note)
                    else:
                        measure.remove(prev_note)
                note.remove(chord)
            prev_note = note
                    
        if remove_voice_tags:
            # strip one voice
            to_remove = measure.findall("note[voice='%d']" % (3-keep))
            to_keep = measure.findall("note[voice='%d']" % keep)
            #print("to_remove:", to_remove)
            to_keep_rank = note_rank(to_keep[-1])
            to_remove_rank = note_rank(to_remove[-1])
            if to_keep_rank is not None and to_remove_rank is not None:
                if to_keep_rank > to_remove_rank:
                    prev_highest_voice = keep
                else:
                    prev_highest_voice = 3 - keep
            for elem in to_remove:
                measure.remove(elem)

        if remove_voice_tags:
            print("REMOVE_VOICE_TAGS")
        if remove_chord_tags:
            print("REMOVE_CHORD_TAGS")
        assert not (remove_voice_tags and remove_chord_tags), "Remove algorithm too simple"


def main():
    if len(sys.argv) != 2:
        print("Usage: voicesplitter.py <music-xml>")
        sys.exit(1)
    filename = sys.argv[1]
    tree = ET.parse(filename)
    root = tree.getroot()
    print(root.tag)
    for c in root:
        print(c.tag, c.attrib)
    #    partnames = root.findall("./part-list/score-part/part-name")
    #    for partname in partnames:
    #        print(partname.text)
    partlist = root.find('part-list')
    basepart_info = root.findall("./part-list/score-part[part-name='Bas']")[0]
    basepart_id = basepart_info.attrib['id']
    print('ID:', basepart_info.attrib['id'])
    basepart = root.findall("./part[@id='%s']" % basepart_id)[0]

    # Rename basepart
    basepart_info.attrib['id'] = 'base_temp'
    basepart.attrib['id'] = 'base_temp'
    # And throw away from XML
    partlist.remove(basepart_info)
    root.remove(basepart)
    

    # Add two new parts
    b1_info = copy.deepcopy(basepart_info)
    b2_info = copy.deepcopy(basepart_info)
    b1_info.attrib['id'] = 'PB1' # Improve!
    b2_info.attrib['id'] = 'PB2' # Improve!
    partlist.append(b1_info)
    partlist.append(b2_info)

    # Easier to copy original measures and just strip out "bad" notes,
    # instead of rebuilding each measure
    #b1 = ET.SubElement(root, 'part', {'id': 'PB1'})
    #b2 = ET.SubElement(root, 'part', {'id': 'PB2'})
    b1 = copy.deepcopy(basepart)
    b2 = copy.deepcopy(basepart)
    b1.attrib['id'] = 'PB1' # Improve!
    b2.attrib['id'] = 'PB2' # Improve!
    root.append(b1)
    root.append(b2)
    
    one_voice(b1, keep=1)
    one_voice(b2, keep=2)
    
    (path, ext) = os.path.splitext(filename)
    tree.write(path + '_base_split' + ext)

main()
