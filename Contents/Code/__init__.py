import urllib
import urllib2 as urllib
import data18

VERSION_NO = '3.2019.09.19.1'
MILISECONDS_PER_SECOND = 1000
def Start():
    #HTTP.ClearCache()
    HTTP.CacheTime = CACHE_1WEEK
    HTTP.Headers['User-agent'] = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)'
    HTTP.Headers['Accept-Encoding'] = 'gzip'

class Data18PhoenixAgent(Agent.Movies):
    name = 'Data18-Phoenix'
    languages = [Locale.Language.English]
    accepts_from = ['com.plexapp.agents.localmedia']
    primary_provider = True

    def search(self, results, media, lang):
        title = media.name
        if media.primary_metadata is not None:
            title = media.primary_metadata.title

        Log('*******MEDIA TITLE****** ' + str(title))

        # Search for year
        year = media.year
        if media.primary_metadata is not None:
            year = media.primary_metadata.year

        encodedTitle = urllib.quote(title)
        Log(encodedTitle)
        searchResults = HTML.ElementFromURL('https://data18.empirestores.co/Search?q=' + encodedTitle)
        searchPage = data18.SearchPage(searchResults)
        for searchResult in searchPage.get_search_results():
            Log(searchResult.get_title())
            titleNoFormatting = searchResult.get_title()
            curID = searchResult.get_details_path().replace('/','_')
            Log(str(curID))
            score = 100 - Util.LevenshteinDistance(title.lower(), titleNoFormatting.lower())
            results.Append(MetadataSearchResult(id = curID, name = titleNoFormatting, score = score, lang = lang))

        results.Sort('score', descending=True)

    def update(self, metadata, media, lang):
        Log('******UPDATE CALLED*******')

        details_path = str(metadata.id).replace('_','/')
        url = 'https://data18.empirestores.co/' + details_path
        detailsPageElements = HTML.ElementFromURL(url)
        detailsPage = data18.DetailsPage(detailsPageElements)
        metadata.title = detailsPage.get_title()
        metadata.studio = detailsPage.get_studio()
        metadata.content_rating = 'NC-17'
        metadata.content_rating_age = 18
        release_date = detailsPage.get_release_date()
        posterURL = detailsPage.get_cover_url()
        Log("PosterURL: " + posterURL)
        metadata.posters[posterURL] = Proxy.Preview(HTTP.Request(posterURL, headers={'Referer': 'http://www.google.com'}).content, sort_order = 1)
        # Handle optional data
        if release_date:
            metadata.originally_available_at = release_date
            metadata.year = release_date.year
        runtime = detailsPage.get_runtime()
        if runtime:
            metadata.duration = int(runtime.total_seconds()) * MILISECONDS_PER_SECOND
        tagline = detailsPage.get_tagline()
        if tagline:
            metadata.tagline = tagline
        summary = detailsPage.get_synopsis()
        if summary:
            metadata.summary = detailsPage.get_synopsis()
        for actor in detailsPage.get_actors():
            role = metadata.roles.new()
            role.name = actor[0]
            role.photo = actor[1]
        metadata.genres.clear()
        metadata.genres.add('Porn')
        for genre in detailsPage.get_categories():
            metadata.genres.add(genre)
        backgroundURL = detailsPage.get_background_url()
        if backgroundURL:
            Log("BackgroundURL: " + backgroundURL)
            metadata.art[backgroundURL] = Proxy.Preview(HTTP.Request(backgroundURL, headers={'Referer': 'http://www.google.com'}).content, sort_order = 1)
