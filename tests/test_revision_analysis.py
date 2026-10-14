import numpy as np
import pytest
from xsentinel.revision.analysis import attack_groups,revised_metrics,catch_miss,fixed_model_cluster_difference


def test_groups_separate_direct_evasion_and_keep_fixed_denominators():
    groups=attack_groups([.9,.8,.2,.9],[.1,.1,.1,.9],[.9,.1,.9,.9])
    assert groups['eligible'].tolist()==[True,True,False,True]
    assert groups['successful_eligible'].tolist()==[True,True,False,False]
    assert groups['paired_new_evasion'].tolist()==[True,False,False,False]
    metrics=revised_metrics([.6,.5,.8,.9],[.5,.6],.5,groups)
    assert metrics['recall_successful_eligible']['count']==1
    assert metrics['recall_successful_eligible']['n']==2
    assert metrics['post_defense_asr']['count']==1 and metrics['post_defense_asr']['n']==3
    assert metrics['benign_fpr']['count']==1 # strict greater; score tie is not an alert
    assert catch_miss([1,0,1,0],[0,1,0,0],groups)['successful_eligible']=={'n':2,'both':0,'first_only':1,'second_only':1,'neither':0}


def test_empty_success_has_no_fake_auc_or_recall():
    groups=attack_groups([.9],[.9],[.9]);metrics=revised_metrics([1],[0],.5,groups)
    assert metrics['auroc_successful_eligible'] is None
    assert metrics['recall_successful_eligible']['rate'] is None
    with pytest.raises(ValueError):attack_groups([1],[float('nan')],[1])


def test_cluster_bootstrap_retains_repeated_source_observations():
    success=np.ones((2,6));eligible=success.copy();first=np.zeros((2,6));second=np.ones((2,6))
    benign=np.zeros((2,5))
    result=fixed_model_cluster_difference(success,eligible,first,second,benign,benign,40,17)
    assert result['recall']['difference']==1 and result['recall']['ci95']==[1,1]
    assert result['post_defense_asr']['difference']==-1
    assert result['benign_fpr']['ci95']==[0,0]
    assert result['malware_sources']==6 # two runs do not manufacture twelve independent sources
    with pytest.raises(ValueError):fixed_model_cluster_difference(success,eligible,first,second[:,:-1],benign,benign)
