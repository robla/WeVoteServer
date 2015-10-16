# candidate/models.py
# Brought to you by We Vote. Be good.
# -*- coding: UTF-8 -*-

from django.db import models
from exception.models import handle_record_found_more_than_one_exception
from wevote_settings.models import fetch_next_we_vote_id_last_candidate_campaign_integer, fetch_site_unique_id_prefix
import wevote_functions.admin
from wevote_functions.models import extract_state_from_ocd_division_id

logger = wevote_functions.admin.get_logger(__name__)


class CandidateCampaignList(models.Model):
    """
    This is a class to make it easy to retrieve lists of Candidates
    """

    def retrieve_candidate_campaigns_for_this_election_list(self):
        candidates_list_temp = CandidateCampaign.objects.all()
        # Order by candidate_name.
        # To order by last name we will need to make some guesses in some case about what the last name is.
        candidates_list_temp = candidates_list_temp.order_by('candidate_name')
        # TODO Temp google_civic_election_id
        # candidates_list_temp = candidates_list_temp.filter(google_civic_election_id=1)
        return candidates_list_temp


class CandidateCampaign(models.Model):
    # The we_vote_id identifier is unique across all We Vote sites, and allows us to share our data with other
    # organizations
    # It starts with "wv" then we add on a database specific identifier like "3v" (WeVoteSetting.site_unique_id_prefix)
    # then the string "cand", and then a sequential integer like "123".
    # We keep the last value in WeVoteSetting.we_vote_id_last_candidate_campaign_integer
    we_vote_id = models.CharField(
        verbose_name="we vote permanent id", max_length=255, default=None, null=True, blank=True, unique=True)
    maplight_id = models.CharField(
        verbose_name="maplight candidate id", max_length=255, default=None, null=True, blank=True, unique=True)
    # The internal We Vote id for the ContestOffice that this candidate is competing for.
    # During setup we need to allow this to be null.
    contest_office_id = models.CharField(
        verbose_name="contest_office_id id", max_length=254, null=True, blank=True)
    # politician link to local We Vote Politician entry. During setup we need to allow this to be null.
    politician_id = models.IntegerField(verbose_name="politician unique identifier", null=True, blank=True)
    # The candidate's name.
    candidate_name = models.CharField(verbose_name="candidate name", max_length=254, null=False, blank=False)
    # The candidate's name as passed over by Google Civic. We save this so we can match to this candidate even
    # if we edit the candidate's name locally.
    google_civic_candidate_name = models.CharField(verbose_name="candidate name exactly as received from google civic",
                                                   max_length=254, null=False, blank=False)
    # The full name of the party the candidate is a member of.
    party = models.CharField(verbose_name="party", max_length=254, null=True, blank=True)
    # A URL for a photo of the candidate.
    photo_url = models.CharField(verbose_name="photoUrl", max_length=254, null=True, blank=True)
    photo_url_from_maplight = models.URLField(verbose_name='candidate portrait url of candidate', blank=True, null=True)
    # The order the candidate appears on the ballot relative to other candidates for this contest.
    order_on_ballot = models.CharField(verbose_name="order on ballot", max_length=254, null=True, blank=True)
    # The unique ID of the election containing this contest. (Provided by Google Civic)
    google_civic_election_id = models.CharField(
        verbose_name="google civic election id", max_length=254, null=True, blank=True)
    ocd_division_id = models.CharField(verbose_name="ocd division id", max_length=254, null=True, blank=True)
    # The URL for the candidate's campaign web site.
    candidate_url = models.URLField(verbose_name='website url of candidate campaign', blank=True, null=True)
    facebook_url = models.URLField(verbose_name='facebook url of candidate campaign', blank=True, null=True)
    twitter_url = models.URLField(verbose_name='twitter url of candidate campaign', blank=True, null=True)
    google_plus_url = models.URLField(verbose_name='google plus url of candidate campaign', blank=True, null=True)
    youtube_url = models.URLField(verbose_name='youtube url of candidate campaign', blank=True, null=True)
    # The email address for the candidate's campaign.
    candidate_email = models.CharField(verbose_name="candidate campaign email", max_length=254, null=True, blank=True)
    # The voice phone number for the candidate's campaign office.
    candidate_phone = models.CharField(verbose_name="candidate campaign phone", max_length=254, null=True, blank=True)
    # The internal We Vote unique ID of the Politician, so we can check data-integrity of imports.
    we_vote_politician_id = models.CharField(
        verbose_name="we vote politician id", max_length=254, null=True, blank=True)

    def fetch_photo_url(self):
        if self.photo_url_from_maplight:
            return self.photo_url_from_maplight
        elif self.photo_url:
            return self.photo_url
        else:
            return ""
            # "http://votersedge.org/sites/all/modules/map/modules/map_proposition/images/politicians/2662.jpg"
        # else:
        #     politician_manager = PoliticianManager()
        #     return politician_manager.fetch_photo_url(self.politician_id)

    def get_candidate_state(self):
        # Pull this from ocdDivisionId
        ocd_division_id = self.ocd_division_id
        return extract_state_from_ocd_division_id(ocd_division_id)

    # We override the save function so we can auto-generate we_vote_id
    def save(self, *args, **kwargs):
        # Even if this data came from another source we still need a unique we_vote_id
        if self.we_vote_id:
            self.we_vote_id = self.we_vote_id.strip()
        if self.we_vote_id == "" or self.we_vote_id is None:  # If there isn't a value...
            # ...generate a new id
            site_unique_id_prefix = fetch_site_unique_id_prefix()
            next_local_integer = fetch_next_we_vote_id_last_candidate_campaign_integer()
            # "wv" = We Vote
            # site_unique_id_prefix = a generated (or assigned) unique id for one server running We Vote
            # "cand" = tells us this is a unique id for a CandidateCampaign
            # next_integer = a unique, sequential integer for this server - not necessarily tied to database id
            self.we_vote_id = "wv{site_unique_id_prefix}cand{next_integer}".format(
                site_unique_id_prefix=site_unique_id_prefix,
                next_integer=next_local_integer,
            )
        if self.maplight_id == "":  # We want this to be unique IF there is a value, and otherwise "None"
            self.maplight_id = None
        super(CandidateCampaign, self).save(*args, **kwargs)


#
def mimic_google_civic_initials(name):
    modified_name = name.replace(' A ', ' A. ')
    modified_name = modified_name.replace(' B ', ' B. ')
    modified_name = modified_name.replace(' C ', ' C. ')
    modified_name = modified_name.replace(' D ', ' D. ')
    modified_name = modified_name.replace(' E ', ' E. ')
    modified_name = modified_name.replace(' F ', ' F. ')
    modified_name = modified_name.replace(' G ', ' G. ')
    modified_name = modified_name.replace(' H ', ' H. ')
    modified_name = modified_name.replace(' I ', ' I. ')
    modified_name = modified_name.replace(' J ', ' J. ')
    modified_name = modified_name.replace(' K ', ' K. ')
    modified_name = modified_name.replace(' L ', ' L. ')
    modified_name = modified_name.replace(' M ', ' M. ')
    modified_name = modified_name.replace(' N ', ' N. ')
    modified_name = modified_name.replace(' O ', ' O. ')
    modified_name = modified_name.replace(' P ', ' P. ')
    modified_name = modified_name.replace(' Q ', ' Q. ')
    modified_name = modified_name.replace(' R ', ' R. ')
    modified_name = modified_name.replace(' S ', ' S. ')
    modified_name = modified_name.replace(' T ', ' T. ')
    modified_name = modified_name.replace(' U ', ' U. ')
    modified_name = modified_name.replace(' V ', ' V. ')
    modified_name = modified_name.replace(' W ', ' W. ')
    modified_name = modified_name.replace(' X ', ' X. ')
    modified_name = modified_name.replace(' Y ', ' Y. ')
    modified_name = modified_name.replace(' Z ', ' Z. ')
    return modified_name


class CandidateCampaignManager(models.Model):

    def __unicode__(self):
        return "CandidateCampaignManager"

    def retrieve_candidate_campaign_from_id(self, candidate_campaign_id):
        candidate_campaign_manager = CandidateCampaignManager()
        return candidate_campaign_manager.retrieve_candidate_campaign(candidate_campaign_id)

    def retrieve_candidate_campaign_from_we_vote_id(self, we_vote_id):
        candidate_campaign_id = 0
        candidate_campaign_manager = CandidateCampaignManager()
        return candidate_campaign_manager.retrieve_candidate_campaign(candidate_campaign_id, we_vote_id)

    def fetch_candidate_campaign_id_from_we_vote_id(self, we_vote_id):
        candidate_campaign_id = 0
        candidate_campaign_manager = CandidateCampaignManager()
        results = candidate_campaign_manager.retrieve_candidate_campaign(candidate_campaign_id, we_vote_id)
        if results['success']:
            return results['candidate_campaign_id']
        return 0

    def retrieve_candidate_campaign_from_maplight_id(self, candidate_maplight_id):
        candidate_campaign_id = 0
        we_vote_id = ''
        candidate_campaign_manager = CandidateCampaignManager()
        return candidate_campaign_manager.retrieve_candidate_campaign(
            candidate_campaign_id, we_vote_id, candidate_maplight_id)

    def retrieve_candidate_campaign_from_candidate_name(self, candidate_name):
        candidate_campaign_id = 0
        we_vote_id = ''
        candidate_maplight_id = ''
        candidate_campaign_manager = CandidateCampaignManager()

        results = candidate_campaign_manager.retrieve_candidate_campaign(
            candidate_campaign_id, we_vote_id, candidate_maplight_id, candidate_name)
        if results['success']:
            return results

        # Try to modify the candidate name, and search again
        # MapLight for example will pass in "Ronald  Gold" for example
        candidate_name_try2 = candidate_name.replace('  ', ' ')
        results = candidate_campaign_manager.retrieve_candidate_campaign(
            candidate_campaign_id, we_vote_id, candidate_maplight_id, candidate_name_try2)
        if results['success']:
            return results

        # MapLight also passes in "Kamela D Harris" for example, and Google Civic uses "Kamela D. Harris"
        candidate_name_try3 = mimic_google_civic_initials(candidate_name)
        if candidate_name_try3 != candidate_name:
            results = candidate_campaign_manager.retrieve_candidate_campaign(
                candidate_campaign_id, we_vote_id, candidate_maplight_id, candidate_name_try3)
            if results['success']:
                return results

        # Otherwise return failed results
        return results

    # NOTE: searching by all other variables seems to return a list of objects
    def retrieve_candidate_campaign(
            self, candidate_campaign_id, we_vote_id=None, candidate_maplight_id=None, candidate_name=None):
        error_result = False
        exception_does_not_exist = False
        exception_multiple_object_returned = False
        candidate_campaign_on_stage = CandidateCampaign()

        try:
            if candidate_campaign_id > 0:
                candidate_campaign_on_stage = CandidateCampaign.objects.get(id=candidate_campaign_id)
                candidate_campaign_id = candidate_campaign_on_stage.id
            elif len(we_vote_id) > 0:
                candidate_campaign_on_stage = CandidateCampaign.objects.get(we_vote_id=we_vote_id)
                candidate_campaign_id = candidate_campaign_on_stage.id
            elif candidate_maplight_id > 0 and candidate_maplight_id != "":
                candidate_campaign_on_stage = CandidateCampaign.objects.get(maplight_id=candidate_maplight_id)
                candidate_campaign_id = candidate_campaign_on_stage.id
            elif len(candidate_name) > 0:
                candidate_campaign_on_stage = CandidateCampaign.objects.get(candidate_name=candidate_name)
                candidate_campaign_id = candidate_campaign_on_stage.id
        except CandidateCampaign.MultipleObjectsReturned as e:
            handle_record_found_more_than_one_exception(e, logger=logger)
            exception_multiple_object_returned = True
        except CandidateCampaign.DoesNotExist:
            exception_does_not_exist = True

        results = {
            'success':                  True if candidate_campaign_id > 0 else False,
            'error_result':             error_result,
            'DoesNotExist':             exception_does_not_exist,
            'MultipleObjectsReturned':  exception_multiple_object_returned,
            'candidate_campaign_found': True if candidate_campaign_id > 0 else False,
            'candidate_campaign_id':    candidate_campaign_id,
            'candidate_campaign':       candidate_campaign_on_stage,
        }
        return results

    def update_or_create_candidate_campaign(self, google_civic_election_id, ocd_division_id, contest_office_id,
                                            candidate_name, updated_candidate_campaign_values):
        """
        Either update or create a candidate_campaign entry.
        """
        exception_multiple_object_returned = False
        new_candidate_campaign_created = False
        candidate_campaign_on_stage = CandidateCampaign()

        if not google_civic_election_id:
            success = False
            status = 'MISSING_ELECTION_ID'
        elif not ocd_division_id:
            success = False
            status = 'MISSING_OCD_DIVISION_ID'
        elif not contest_office_id:
            success = False
            status = 'MISSING_CONTEST_OFFICE_ID'
        elif not candidate_name:
            success = False
            status = 'MISSING_CANDIDATE_NAME'
        else:
            try:
                # TODO Strictly speaking we shouldn't update candidate_name so we can change it elsewhere
                candidate_campaign_on_stage, new_candidate_campaign_created = \
                    CandidateCampaign.objects.update_or_create(
                        google_civic_election_id__exact=google_civic_election_id,
                        ocd_division_id__exact=ocd_division_id,
                        contest_office_id__exact=contest_office_id,
                        google_civic_candidate_name__exact=candidate_name,
                        defaults=updated_candidate_campaign_values)
                success = True
                status = 'CANDIDATE_CAMPAIGN_SAVED'
            except CandidateCampaign.MultipleObjectsReturned as e:
                handle_record_found_more_than_one_exception(e, logger=logger)
                success = False
                status = 'MULTIPLE_MATCHING_CANDIDATE_CAMPAIGNS_FOUND'
                exception_multiple_object_returned = True

        results = {
            'success':                          success,
            'status':                           status,
            'MultipleObjectsReturned':          exception_multiple_object_returned,
            'new_candidate_campaign_created':   new_candidate_campaign_created,
            'candidate_campaign':               candidate_campaign_on_stage,
        }
        return results