# A dictionary of movie critics and their ratings of a small
# set of movies
from math import sqrt
from numpy import dot
from numpy.linalg import norm


# Jaccard Distance (A, B) = |A intersection B| / |A union B|
def sim_jaccard(prefs, person1, person2):
    # Get the list of shared_items
    p1_intersect_p2 = {}
    for item in prefs[person1]:
        if item in prefs[person2]:
            p1_intersect_p2[item] = 1

    # Get the list of all items that we have
    p1_union_p2 = dict(prefs[person1])
    for item in prefs[person2]:
        if item not in p1_union_p2:
            p1_union_p2[item] = 1

    #Get the total number of items for intersection and union
    p1_intersect_p2, p1_union_p2 = len(p1_intersect_p2), len(p1_union_p2)

    # return jaccard distance
    return float(p1_intersect_p2) / float(p1_union_p2)


def sim_cosine(prefs, person1, person2):
    # Get the list of shared_items
    person1_criticscores = []
    person2_criticscores = []
    si = set()

    for item in prefs[person1]:
        if item in prefs[person2]:
            si.add(item)
            person1_criticscores.append(prefs[person1][item])
            person2_criticscores.append(prefs[person2][item])

    # if they have no ratings in common, return 0
    if len(si) == 0:
        return 0
    
    cosine = dot(person1_criticscores, person2_criticscores) / \
        (norm(person1_criticscores) * norm(person2_criticscores))

    return cosine
 

def sim_tanimoto(prefs, person1, person2):
    # Construct the set of all items
    all_items = set()
    for person in prefs:
        for movie in prefs[person]:
            all_items.add(movie)

    # Below lines are with traditional loop and iteration.
    pSum = 0
    sumsq1 = 0
    sumsq2 = 0
    for item in all_items:
        a = 1 if item in prefs[person1] else 0
        b = 1 if item in prefs[person2] else 0
        pSum = pSum + a*b
        sumsq1 = sumsq1 + a*a
        sumsq2 = sumsq2 + b*b

    # The above loop with list Comprehension.
    # pSum = sum([1 for item in all_items if item in prefs[person1] and item in prefs[person2]])
    # sumsq1 = sum([1 for item in all_items if item in prefs[person1]])
    # sumsq2 = sum([1 for item in all_items if item in prefs[person2]])

    return pSum / (sumsq1 + sumsq2 - pSum)

def sim_distance(prefs, person1, person2):
    # Get the list of shared_items
    si = {}
    for item in prefs[person1]:
        if item in prefs[person2]:
            si[item] = 1

    # if they have no ratings in common, return 0
    if len(si) == 0:
        return 0

    # Add up the squares of all the differences
    sum_of_squares = sum([pow(prefs[person1][item] - prefs[person2][item], 2)
                          for item in prefs[person1] if item in prefs[person2]])

    return 1 / (1 + sqrt(sum_of_squares))


# Returns the Pearson correlation coefficient for p1 and p2
def sim_pearson(prefs, p1, p2):
    # Get the list of mutually rated items
    si = {}
    for item in prefs[p1]:
        if item in prefs[p2]:
            si[item] = 1

    # if they are no ratings in common, return 0
    if len(si) == 0:
        return 0

    # Sum calculations
    n = len(si)

    # Sums of all the preferences
    sum1 = sum([prefs[p1][it] for it in si])
    sum2 = sum([prefs[p2][it] for it in si])

    # Sums of the squares
    sum1Sq = sum([pow(prefs[p1][it], 2) for it in si])
    sum2Sq = sum([pow(prefs[p2][it], 2) for it in si])

    # Sum of the products
    pSum = sum([prefs[p1][it] * prefs[p2][it] for it in si])

    # Calculate r (Pearson score)
    num = pSum - (sum1 * sum2 / n)
    den = sqrt((sum1Sq - pow(sum1, 2) / n) * (sum2Sq - pow(sum2, 2) / n))
    if den == 0:
        return 0

    r = num / den

    return r


# Returns the best matches for person from the prefs dictionary.
# Number of results and similarity function are optional params.
def topMatches(prefs, person, n=5, similarity=sim_pearson):
    scores = [(similarity(prefs, person, other), other)
              for other in prefs if other != person]
    scores.sort()
    scores.reverse()
    return scores


# Gets recommendations for a person by using a weighted average
# of every other user's rankings
def getRecommendations(prefs, person, similarity=sim_pearson):
    totals = {}
    simSums = {}
    for other in prefs:
        # don't compare me to myself
        if other == person:
            continue
        sim = similarity(prefs, person, other)
        # ignore scores of zero or lower
        if sim <= 0:
            continue
        for item in prefs[other]:
            # only score movies I haven't seen yet
            if item not in prefs[person] or prefs[person][item] == 0:
                # Similarity * Score
                totals.setdefault(item, 0)
                totals[item] += prefs[other][item] * sim
                # Sum of similarities
                simSums.setdefault(item, 0)
                simSums[item] += sim

    # Create the normalized list
    rankings = [(total / simSums[item], item)
                for item, total in totals.items()]

    # Return the sorted list
    rankings.sort()
    rankings.reverse()
    return rankings


def transformPrefs(prefs):
    result = {}
    for person in prefs:
        for item in prefs[person]:
            result.setdefault(item, {})

            # Flip item and person
            result[item][person] = prefs[person][item]
    return result


def calculateSimilarItems(prefs, n=10, similarity=sim_distance):
    # Create a dictionary of items showing which other items they
    # are most similar to.
    result = {}
    # Invert the preference matrix to be item-centric
    itemPrefs = transformPrefs(prefs)
    c = 0
    for item in itemPrefs:
        # Status updates for large datasets
        c += 1
        if c % 100 == 0:
            print("%d / %d" % (c, len(itemPrefs)))
        # Find the most similar items to this one
        scores = topMatches(itemPrefs, item, n=n, similarity=similarity)
        result[item] = scores
    return result


def getRecommendedItems(prefs, itemMatch, user):
    userRatings = prefs[user]
    scores = {}
    totalSim = {}
    # Loop over items rated by this user
    for (item, rating) in userRatings.items():

        # Loop over items similar to this one
        for (similarity, item2) in itemMatch[item]:

            # Ignore if this user has already rated this item
            if item2 in userRatings:
                continue
            # Weighted sum of rating times similarity
            scores.setdefault(item2, 0)
            scores[item2] += similarity * rating
            # Sum of all the similarities
            totalSim.setdefault(item2, 0)
            totalSim[item2] += similarity

    # Divide each total score by total weighting to get an average
    rankings = [(score / totalSim[item], item)
                for item, score in scores.items()]

    # Return the rankings from highest to lowest
    rankings.sort()
    rankings.reverse()
    return rankings
