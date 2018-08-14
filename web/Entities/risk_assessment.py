

class Risk_assessment(object):
    '''
    This class represents a row entry in the DB table for 'RISK_ASSESSMENT'
    '''

    datetime_tname            = 'datetime'
    patient_id_tname          = 'patient_id'
    weight_tname              = 'weight'
    mbs_normal_tname          = 'mbs_normal'
    mbs_confusion_tname       = 'mbs_confusion'
    mbs_restlessness_tname    = 'mbs_restlessness'
    mbs_agitation_tname       = 'mbs_agitation'
    mbs_uncooperative_tname   = 'mbs_uncooperative'
    mbs_hallucination_tname   = 'mbs_hallucination'
    mbs_drowsy_tname          = 'mbs_drowsy'
    mbs_others_tname          = 'mbs_others'
    ast_medication_tname      = 'ast_medication'
    ast_clothes_tname         = 'ast_clothes'
    ast_eating_tname          = 'ast_eating'
    ast_bathing_tname         = 'ast_bathing'
    ast_walking_tname         = 'ast_walking'
    ast_toileting_tname       = 'ast_toileting'
    ast_others_tname          = 'ast_others'
    pain_none_tname           = 'pain_none'
    pain_general_tname        = 'pain_general'
    pain_joint_tname          = 'pain_joint'
    pain_critical_tname       = 'pain_critical'
    pain_other_tname          = 'pain_other'
    num_medication_tname      = 'num_medication'
    hearing_ability_tname     = 'hearing_ability'       # 1-5 : reduce drastically - stable
    vision_ability_tname      = 'vision_ability'        # 1-5 : reduce drastically - stable 
    mobility_tname            = 'mobility'              # 1-5 : reduce drastically - stable
    dependency_tname          = 'dependency'            # 1-5 : dependent - independent
    dependency_comments_tname = 'dependency_comments'   

    tname_list = [datetime_tname, patient_id_tname, weight_tname, mbs_normal_tname, mbs_confusion_tname, mbs_restlessness_tname, \
                  mbs_agitation_tname, mbs_uncooperative_tname, mbs_hallucination_tname, mbs_drowsy_tname, mbs_others_tname, \
                  ast_medication_tname, ast_clothes_tname, ast_eating_tname, ast_bathing_tname, ast_walking_tname, ast_toileting_tname, \
                  ast_others_tname, pain_none_tname, pain_general_tname, pain_joint_tname, pain_critical_tname, pain_other_tname, num_medication_tname, \
                  hearing_ability_tname, vision_ability_tname, mobility_tname, dependency_tname, dependency_comments_tname]

    NUM_MEDICATION_MAPPING = {0: '0',
                              1: '1 - 2',
                              2: '3 - 4',
                              3: '>=5'}

    def __init__(self, datetime, patient_id, weight=None, mbs_normal=False,                  \
                mbs_confusion=False, mbs_restlessness=False, mbs_agitation=False,            \
                mbs_uncooperative=False, mbs_hallucination=False, mbs_drowsy=False,          \
                mbs_others=None, ast_medication=False, ast_clothes=False, ast_eating=False, \
                ast_bathing=False, ast_walking=False, ast_toileting=False,ast_others=None, pain_none=False,  \
                pain_general=False, pain_joint=False, pain_critical=False, pain_other=None, \
                num_medication=None, hearing_ability=None, vision_ability=None,              \
                mobility=None, dependency=None, dependency_comments=None):
        '''
        Constructor
        '''

        self.datetime           = datetime + '-01 00:00:00'              # datetime
        self.patient_id         = patient_id            # int
        self.weight             = weight                # float
        self.mbs_normal         = mbs_normal            # bool
        self.mbs_confusion      = mbs_confusion         # bool
        self.mbs_restlessness   = mbs_restlessness      # bool
        self.mbs_agitation      = mbs_agitation         # bool
        self.mbs_uncooperative  = mbs_uncooperative     # bool
        self.mbs_hallucination  = mbs_hallucination     # bool
        self.mbs_drowsy         = mbs_drowsy            # bool
        self.mbs_others         = mbs_others            # str
        self.ast_medication     = ast_medication        # bool
        self.ast_clothes        = ast_clothes           # bool
        self.ast_eating         = ast_eating            # bool
        self.ast_bathing        = ast_bathing           # bool
        self.ast_walking        = ast_walking           # bool
        self.ast_toileting      = ast_toileting         # bool
        self.ast_others         = ast_others        # bool
        self.pain_none          = pain_none             # bool
        self.pain_general       = pain_general          # bool
        self.pain_joint         = pain_joint            # bool
        self.pain_critical      = pain_critical         # bool
        self.pain_other         = pain_other            # bool
        self.num_medication     = num_medication        # int
        self.hearing_ability    = hearing_ability       # int
        self.vision_ability     = vision_ability        # int
        self.mobility           = mobility              # int
        self.dependency         = dependency            # int
        self.dependency_comments = dependency_comments  # str

        self.tname_list = []
        self.var_list = [self.datetime, self.patient_id, self.weight, self.mbs_normal, self.mbs_confusion, self.mbs_restlessness,           \
                         self.mbs_agitation, self.mbs_uncooperative, self.mbs_hallucination, self.mbs_drowsy, self.mbs_others, self.ast_medication, self.ast_clothes,     \
                         self.ast_eating, self.ast_bathing, self.ast_walking, self.ast_toileting,self.ast_others, self.pain_none, self.pain_general, self.pain_joint, self.pain_critical, \
                         self.pain_other, self.num_medication, self.hearing_ability, self.vision_ability, self.mobility, self.dependency, self.dependency_comments]