import json
from pathlib import Path
from django.core.management.base import BaseCommand
from evaluations.models import Section, SubSection, Criterion
class Command(BaseCommand):
    help='Import all official hotel classification criteria codes from embedded JSON'
    def handle(self,*args,**kwargs):
        data=json.loads((Path(__file__).resolve().parents[2]/'hotel_criteria_full.json').read_text(encoding='utf-8'))
        for n,row in enumerate(data,1):
            sec,_=Section.objects.update_or_create(code=row['section_code'], defaults={'title':row['section_title'],'order':int(row['section_code']) if row['section_code'].isdigit() else n})
            sub,_=SubSection.objects.update_or_create(code=row['subsection_code'], defaults={'section':sec,'title':row['subsection_title'],'order':n})
            Criterion.objects.update_or_create(code=row['code'], defaults={'subsection':sub,'title':row['title'],'one_star':row['one_star'],'two_star':row['two_star'],'three_star':row['three_star'],'four_star':row['four_star'],'five_star':row['five_star'],'corrective_action':row['corrective_action'],'order':n,'active':True})
        self.stdout.write(self.style.SUCCESS(f'Imported/updated {len(data)} criteria'))
