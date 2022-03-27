"""
Definition of views.
"""

from django.shortcuts import render
from django.http import HttpRequest, JsonResponse, HttpResponseRedirect
from django.http.response import HttpResponse
from django.template import RequestContext
from datetime import datetime
from django.views import View
from django.http import FileResponse
from django.views.generic.edit import FormView
from .forms import UploadFileForm
from django.views.decorators.csrf import ensure_csrf_cookie
from app.models import MasterFiles, SubtitlesFiles
from difflib import SequenceMatcher
from collections import defaultdict
from distutils import dir_util
#from channels import Group
import distutils
import shutil, os, re
import mimetypes
from django.conf import settings

LanguageDictionary = {'af': 'afrikaans', 'sq': 'albanian', 'am': 'amharic', 'ar': 'arabic', 'hy': 'armenian',
                      'az': 'azerbaijani', 'eu': 'basque', 'be': 'belarusian', 'bn': 'bengali', 'bs': 'bosnian',
                      'bg': 'bulgarian', 'ca': 'catalan', 'ceb': 'cebuano', 'ny': 'chichewa',
                      'zh-cn': 'chinese (simplified)', 'zh-tw': 'chinese (traditional)', 'co': 'corsican',
                      'hr': 'croatian', 'cs': 'czech', 'da': 'danish', 'nl': 'dutch', 'en': 'english',
                      'eo': 'esperanto', 'et': 'estonian', 'tl': 'filipino', 'fi': 'finnish', 'fr': 'french',
                      'fy': 'frisian', 'gl': 'galician', 'ka': 'georgian', 'de': 'german', 'el': 'greek',
                      'gu': 'gujarati', 'ht': 'haitian creole', 'ha': 'hausa', 'haw': 'hawaiian', 'iw': 'hebrew',
                      'hi': 'hindi', 'hmn': 'hmong', 'hu': 'hungarian', 'is': 'icelandic', 'ig': 'igbo',
                      'id': 'indonesian', 'ga': 'irish', 'it': 'italian', 'ja': 'japanese', 'jw': 'javanese',
                      'kn': 'kannada', 'kk': 'kazakh', 'km': 'khmer', 'ko': 'korean', 'ku': 'kurdish (kurmanji)',
                      'ky': 'kyrgyz', 'lo': 'lao', 'la': 'latin', 'lv': 'latvian', 'lt': 'lithuanian',
                      'lb': 'luxembourgish', 'mk': 'macedonian', 'mg': 'malagasy', 'ms': 'malay', 'ml': 'malayalam',
                      'mt': 'maltese', 'mi': 'maori', 'mr': 'marathi', 'mn': 'mongolian', 'my': 'myanmar (burmese)',
                      'ne': 'nepali', 'no': 'norwegian', 'ps': 'pashto', 'fa': 'persian', 'pl': 'polish',
                      'pt': 'portuguese', 'pa': 'punjabi', 'ro': 'romanian', 'ru': 'russian', 'sm': 'samoan',
                      'gd': 'scots gaelic', 'sr': 'serbian', 'st': 'sesotho', 'sn': 'shona', 'sd': 'sindhi',
                      'si': 'sinhala', 'sk': 'slovak', 'sl': 'slovenian', 'so': 'somali', 'es': 'spanish',
                      'su': 'sundanese', 'sw': 'swahili', 'sv': 'swedish', 'tg': 'tajik', 'ta': 'tamil', 'te': 'telugu',
                      'th': 'thai', 'tr': 'turkish', 'uk': 'ukrainian', 'ur': 'urdu', 'uz': 'uzbek', 'vi': 'vietnamese',
                      'cy': 'welsh', 'xh': 'xhosa', 'yi': 'yiddish', 'yo': 'yoruba', 'zu': 'zulu', 'fil': 'Filipino',
                      'he': 'Hebrew'}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@ensure_csrf_cookie
def upload_multiple_files(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST or None, request.FILES)
        master_files = request.FILES.getlist('files')
        short_files = request.FILES.getlist('shortfiles')
        if not form.errors:
            for m in master_files:
                file = MasterFiles(files = m)
                file.save()
            pass
            for m in short_files:
                file = SubtitlesFiles(files = m)
                file.save()
            pass
            downloadfilepath = file_conversion(master_files,short_files)
            deletefolder()
            context = {'msg' : '<span style="color: green;">File successfully uploaded</span>','file':downloadfilepath}
            return render(request, "app/index.html", context)
    else:
        try:
            os.unlink(os.path.abspath(os.path.join(BASE_DIR, 'media\subtitlefile_bundles.zip')))
        except Exception as E:
            print(E)
        pass
        deletefolder()
        form = UploadFileForm()
    return render(request, 'app/index.html', {'form': form})

def download_zip(request):
    response = ''
    try:
        downloadfilepath = os.path.abspath(os.path.join(BASE_DIR, 'media'))+'\\'+'subtitlefile_bundles.zip'
        if os.path.exists(downloadfilepath):
          file=open(downloadfilepath,'rb')
          response =FileResponse(file)
          response['Content-Type']='application/zip'
          response['Content-Disposition']='attachment;filename="subtitlefile_bundles.zip"'
    except Exception as E:
          print(E)
    pass
    return response
 
def get_groups(seq, group_by):
    print('into the Groups')
    data = []
    for line in seq:
        if len(line) == 1:
            if data:
                yield data
                data = []
        data.append(line)
    if data:
        yield data
    pass

def file_conversion(ListofMasterFiles,ListofSubtitlesFiles):
    MainTimeCodes = []
    if len(ListofSubtitlesFiles) > 0:
        FileIndexDictionary = defaultdict(list)
        FileLineDictionary = defaultdict(list)
        for key, value in LanguageDictionary.items():
            # print("Language Key:{0} & Language Value:{1}".format(key, value))
            if key.__contains__('en'):
                file = 0
                MasterFileName = ""
                while file < len(ListofMasterFiles):
                    if ListofMasterFiles[file].name.lower().__contains__(value.lower()):
                        MasterFileName = os.path.abspath(os.path.join(BASE_DIR, 'media\MasterFiles\\'+ListofMasterFiles[file].name.replace(' ','_')))
                        print('Selected File:{}'.format(MasterFileName))
                    pass
                    file += 1
                pass
                # This Code Required always English Language
                if len(FileIndexDictionary.keys()) == 0:
                    File = 0
                    while File < len(ListofSubtitlesFiles):
                        Remain = len(ListofSubtitlesFiles) - File
                        print('\t\t\t--------------------------')
                        print('\t\t\t Loading:{} & Remaining:{}'.format(File + 1, Remain - 1))
                        print('\t\t\t--------------------------')
                        print('File:{}'.format(ListofSubtitlesFiles[File].name))
                        TextBlock = []
                        FilePath=os.path.abspath(os.path.join(BASE_DIR, 'media\SubtitlesFiles'+'\\'+ListofSubtitlesFiles[File].name.replace(' ','_')))
                        print('File Path:{}'.format(FilePath))
                        with open(os.path.abspath(FilePath), 'r', errors='ignore') as f:
                            for i, group in enumerate(get_groups(f, " "), start=1):
                                TextBlock.append("".join(group))
                            pass
                        pass
                        SplitedTimeCodes = []
                        PureText = []
                        for Tb in TextBlock:
                            SplitedText = []
                            for t in Tb.split('\n')[0:-1]:
                                if not t.__contains__('00:'):
                                    if not t.isdigit():
                                        SplitedText.append(t.strip())
                                    pass
                                pass
                            pass
                            for t in Tb.split('\n')[0:-1]:
                                if t.__contains__(':'):
                                    if t.__contains__('00:'):
                                        SplitedTimeCodes.append(t.strip())
                                    pass
                                pass
                            pass
                            PureText.append(" ".join(SplitedText))
                        pass
                        MainTimeCodes.append(SplitedTimeCodes)
                        StartEndText = [PureText[0], PureText[-1]]
                        Terminal = 0
                        while Terminal <= 1:
                            index = 0
                            with open(MasterFileName, "r", errors='ignore') as ins:
                                lines = ins.readlines()
                                for line in range(0, len(lines)):
                                    if not lines[line].__contains__('00:'):
                                        try:
                                            if SequenceMatcher(None,lines[line].lower().replace('\n', '').encode('ascii','ignore').strip() +lines[line + 1].lower().replace('\n', '').encode('ascii', 'ignore').strip(),StartEndText[Terminal].lower().replace('\n', '').encode('ascii', 'ignore').strip()).ratio() > 0.9:
                                                #print('Master File Text:{}'.format(lines[line].lower().replace('\n', '').encode('ascii', 'ignore') +lines[line + 1].lower().replace('\n', '').encode('ascii', 'ignore')))
                                                #print('Short File Text:{} & Index:{}'.format(StartEndText[Terminal].lower().replace('\n', '').encode('ascii','ignore'),index))
                                                IndexLinenumber = line
                                                while IndexLinenumber > 0:
                                                    if lines[IndexLinenumber].replace('\n', '').strip().isdigit():
                                                        #print("Line Number:{}".format(lines[IndexLinenumber]))
                                                        FileLineDictionary[File + 1].append(int(lines[IndexLinenumber].replace('\n','')))
                                                        break
                                                    pass
                                                    IndexLinenumber -= 1
                                                pass
                                                FileIndexDictionary[File + 1].append(index)
                                                break
                                            elif SequenceMatcher(None, re.sub('[^A-Za-z]+', ' ',lines[line].lower().replace('\n','').encode('ascii', 'ignore').decode('utf-8')) + re.sub('[^A-Za-z]+', ' ',lines[line + 1].lower().replace('\n','').encode('ascii','ignore').decode('utf-8')),re.sub('[^A-Za-z]+', ' ',StartEndText[Terminal].lower().replace('\n','').encode('ascii', 'ignore').strip().decode('utf-8'))).ratio() > 0.8:
                                                print('Master File Text:{}'.format(lines[line].lower().replace('\n', '').encode('ascii','ignore').decode('utf-8') + re.sub('[^A-Za-z]+', ' ',lines[line + 1].lower().replace('\n','').encode('ascii', 'ignore').decode('utf-8'))))
                                                print('Short File Text:{} & Index:{}'.format(StartEndText[Terminal].lower().replace('\n', '').encode('ascii','ignore'),index))
                                                IndexLinenumber = line
                                                while IndexLinenumber > 0:
                                                    if lines[IndexLinenumber].replace('\n', '').strip().isdigit():
                                                        #print("Line Number:{}".format(lines[IndexLinenumber]))
                                                        FileLineDictionary[File + 1].append(int(lines[IndexLinenumber].replace('\n','')))
                                                        break
                                                    pass
                                                    IndexLinenumber -= 1
                                                pass
                                                FileIndexDictionary[File + 1].append(index)
                                                break
                                            pass
                                        except Exception as E:
                                            print(E)
                                        pass
                                    pass
                                    index += 1
                                pass
                            pass
                            Terminal += 1
                        pass
                        File += 1
                    pass
                pass
            pass
        pass
        # Now Start Making Subtitles File
        for key, value in LanguageDictionary.items():
            if not key.__contains__('en'):
                file = 0
                MasterFileName = ""
                while file < len(ListofMasterFiles):
                    if ListofMasterFiles[file].name.lower().__contains__(value.lower()):
                        MasterFileName = os.path.abspath(os.path.join(BASE_DIR, 'media\MasterFiles\\'+ListofMasterFiles[file].name.replace(' ','_')))
                    pass
                    file += 1
                pass
                if len(FileLineDictionary.keys()) > 0:
                    res = {key: sorted(FileLineDictionary[key]) for key in sorted(FileLineDictionary)}
                    try:
                        FileIndexer = 0
                        for k, v in res.items():
                            StartIndex = int(v[0])
                            EndIndex = int(v[1])
                            ExtractedData = []
                            with open(MasterFileName, 'r', encoding='cp437',errors='ignore') as file:
                                lines = file.readlines()
                                for line in range(0, len(lines)):
                                    if lines[line].replace('\n', '').strip().isdigit():
                                        if int(lines[line]) == StartIndex:
                                            liner = False
                                            while not liner:
                                                if lines[line].replace('\n', '').strip().isdigit():
                                                    if int(lines[line]) != EndIndex:
                                                        ExtractedData.append(lines[line])
                                                    else:
                                                        ExtractedData.append(lines[line])
                                                        ExtractedData.append(lines[line+1])
                                                        ExtractedData.append(lines[line+2])
                                                        ExtractedData.append(lines[line+3])
                                                        liner = True
                                                    pass
                                                else:
                                                    ExtractedData.append(lines[line])
                                                line += 1
                                            pass
                                            break
                                        pass
                                    pass
                                pass
                                file.seek(0)
                            pass
                            GeneratingFolderFile(ExtractedData, ListofSubtitlesFiles[FileIndexer].name, value,
                                                 MainTimeCodes[FileIndexer])
                            FileIndexer += 1
                        pass
                    except:
                        pass
                pass
            pass
        pass
        downloadfilepath=''
        try:
            for file in os.scandir(os.path.abspath(os.path.join(BASE_DIR, 'media\SubtitlesFiles'))):
               if file.name.endswith(".srt"):
                 os.unlink(file.path)
               pass
            pass
        except Exception as E:
            print(E)
        pass
        try:
            shutil.make_archive(os.path.abspath(os.path.join(BASE_DIR, 'media'))+'\\'+'subtitlefile_bundles', 'zip', os.path.abspath(os.path.join(BASE_DIR, 'media\SubtitlesFiles')))
            downloadfilepath = os.path.abspath(os.path.join(BASE_DIR, 'media'))+'\\'+'subtitlefile_bundles.zip'
            print('Converted to Zip Successfully')
            deletefolder()
        except Exception as E:
            print(E)
        pass
        print('\t\t\t  All Files Converted Successfully!\n\t\t\t   Now you can close Window!')
    pass
    return downloadfilepath
    pass

def deletefolder():
     try:
         shutil.rmtree(os.path.join(BASE_DIR, 'media')+'/MasterFiles', ignore_errors=True)
         shutil.rmtree(os.path.join(BASE_DIR, 'media')+'/SubtitlesFiles', ignore_errors=True)
     except Exception as E:
         print(E)
     pass

def GeneratingFolderFile(ExtractedData, CurrentSubtitleFileName, CurrentLanguage, TimeCodes):
    try:
        distutils.dir_util.mkpath(os.path.abspath(os.path.join(BASE_DIR, 'media\SubtitlesFiles'+'\\'+CurrentLanguage)))
    except:
        pass
    try:
        f = open(os.path.abspath(os.path.join(BASE_DIR, 'media\SubtitlesFiles'+'\\'+CurrentLanguage+"\\"+CurrentSubtitleFileName)), "a", encoding='cp437',
                 errors='ignore')
        line = 1
        Codes = 0
        Digit = False
        for d in ExtractedData:
            if d.replace('\n', '').strip().isdigit():
                f.write(str(line) + '\n')
                line += 1
                Digit = True
            elif Digit:
                if d.__contains__('00:'):
                    d = d.replace(d, TimeCodes[Codes])
                    f.write(d + '\n')
                    Codes += 1
                else:
                    f.write(d)
        pass
        f.close()
    except Exception as E:
        print("\t\t\t    Unable to Save Data:{}".format(E))
    pass
    pass
