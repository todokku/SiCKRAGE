<%inherit file="../layouts/main.mako"/>
<%!
    import datetime

    import sickrage
    from sickrage.core.tv.show.helpers import get_show_list
    from sickrage.core.common import SKIPPED, WANTED, UNAIRED, ARCHIVED, IGNORED, SNATCHED, SNATCHED_PROPER, SNATCHED_BEST, FAILED
    from sickrage.core.common import Overview, Quality, qualityPresets, qualityPresetStrings
    from sickrage.core.helpers import srdatetime
%>
<%block name="content">
    <% totalWanted = totalQual = 0 %>

    % for curShow in get_show_list():
        % if curShow.paused:
            <% continue %>
        % endif

        <% totalWanted = totalWanted + showCounts[curShow.indexer_id][Overview.WANTED] %>
        <% totalQual = totalQual + showCounts[curShow.indexer_id][Overview.QUAL] %>
    % endfor

    <div class="row">
        <div class="col-lg-10 mx-auto">
            <div class="card">
                <div class="card-header">
                    <h3 class="float-md-left">${title}</h3>
                    <div class="float-md-right">
                        <span class="badge wanted">${_('Wanted:')} <b>${totalWanted}</b></span>
                        <span class="badge qual">${_('Low Quality:')} <b>${totalQual}</b></span>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-12">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text">
                                        <span class="fas fa-binoculars"></span>
                                    </span>
                                </div>
                                <select id="pickShow" class="form-control form-control-inline"
                                        title="${_('Choose show')}">
                                    % for curShow in sorted(get_show_list(), key=lambda x: x.name):
                                        % if curShow.paused:
                                            <% continue %>
                                        % endif

                                        % if showCounts[curShow.indexer_id][Overview.QUAL] + showCounts[curShow.indexer_id][Overview.WANTED] != 0:
                                            <option value="${curShow.indexer_id}">${curShow.name}</option>
                                        % endif
                                    % endfor
                                </select>
                            </div>
                        </div>
                    </div>

                    <br/>

                    <div class="row">
                        <div class="col-md-12">
                            <div class="table-responsive">
                                % for curShow in sorted(get_show_list(), key=lambda x: x.name):
                                    % if curShow.paused:
                                        <% continue %>
                                    % endif

                                    % if not showCounts[curShow.indexer_id][Overview.QUAL] + showCounts[curShow.indexer_id][Overview.WANTED] == 0:
                                    <table class="table mb-3">
                                        <tr class="seasonheader" id="show-${curShow.indexer_id}">
                                            <td colspan="3" class="align-left">
                                                <div class="float-md-left">
                                                    <h2>
                                                        <a href="${srWebRoot}/home/displayShow?show=${curShow.indexer_id}">${curShow.name}</a>
                                                    </h2>
                                                </div>
                                                <div class="text-center float-md-right">
                                                        <span class="badge wanted">${_('Wanted:')}
                                                            <b>${showCounts[curShow.indexer_id][Overview.WANTED]}</b></span>
                                                    <span class="badge qual">${_('Low Quality:')}
                                                        <b>${showCounts[curShow.indexer_id][Overview.QUAL]}</b></span>
                                                    <a class="btn forceBacklog"
                                                       href="${srWebRoot}/manage/backlogShow?indexer_id=${curShow.indexer_id}"><i
                                                            class="icon-play-circle icon-white"></i> ${_('Force Backlog')}
                                                    </a>
                                                </div>
                                            </td>
                                        </tr>

                                        <tr class="seasoncols">
                                            <th>${_('Episode')}</th>
                                            <th>${_('Name')}</th>
                                            <th class="text-nowrap">${_('Airdate')}</th>
                                        </tr>

                                    % for curResult in showResults[curShow.indexer_id]:
                                        <% whichStr = '{}x{}'.format(curResult.season, curResult.episode) %>
                                        <% overview = showCats[curShow.indexer_id][whichStr] %>
                                        % if overview in (Overview.QUAL, Overview.WANTED):
                                            <tr class="seasonstyle ${Overview.overviewStrings[showCats[curShow.indexer_id][whichStr]]}">
                                                <td class="tableleft" align="center">${whichStr}</td>
                                                <td class="tableright" align="center" class="text-nowrap">
                                                    ${curResult.name}
                                                </td>
                                                <td>
                                                    <% airDate = srdatetime.SRDateTime(sickrage.app.tz_updater.parse_date_time(curResult.airdate, curShow.airs, curShow.network), convert=True).dt %>
                                                    % if curResult.airdate > datetime.date.min:
                                                        <time datetime="${airDate.isoformat()}"
                                                              class="date">${srdatetime.SRDateTime(airDate).srfdatetime()}</time>
                                                    % else:
                                                        Never
                                                    % endif
                                                </td>
                                            </tr>
                                        % endif
                                    % endfor
                                    % endif
                                    </table>
                                % endfor
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</%block>
