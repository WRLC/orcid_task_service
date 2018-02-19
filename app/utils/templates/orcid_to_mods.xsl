<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns="http://www.loc.gov/mods/v3" xmlns:mods="http://www.loc.gov/mods/v3" xmlns:xlink="http://www.w3.org/1999/xlink"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0" xmlns:internal="http://www.orcid.org/ns/internal" xmlns:funding="http://www.orcid.org/ns/funding" xmlns:preferences="http://www.orcid.org/ns/preferences" xmlns:address="http://www.orcid.org/ns/address" xmlns:education="http://www.orcid.org/ns/education" xmlns:work="http://www.orcid.org/ns/work" xmlns:deprecated="http://www.orcid.org/ns/deprecated" xmlns:other-name="http://www.orcid.org/ns/other-name" xmlns:history="http://www.orcid.org/ns/history" xmlns:employment="http://www.orcid.org/ns/employment" xmlns:error="http://www.orcid.org/ns/error" xmlns:common="http://www.orcid.org/ns/common" xmlns:person="http://www.orcid.org/ns/person" xmlns:activities="http://www.orcid.org/ns/activities" xmlns:record="http://www.orcid.org/ns/record" xmlns:researcher-url="http://www.orcid.org/ns/researcher-url" xmlns:peer-review="http://www.orcid.org/ns/peer-review" xmlns:personal-details="http://www.orcid.org/ns/personal-details" xmlns:bulk="http://www.orcid.org/ns/bulk" xmlns:external-identifier="http://www.orcid.org/ns/external-identifier" xmlns:keyword="http://www.orcid.org/ns/keyword" xmlns:email="http://www.orcid.org/ns/email" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" exclude-result-prefixes="internal funding preferences address education work deprecated other-name history employment error common person activities record researcher-url peer-review personal-details bulk external-identifier keyword email">

<xsl:output encoding="UTF-8" indent="yes" method="xml" standalone="yes"/>
	<!-- top level elements ELEMENT DISS_description (DISS_title,DISS_dates,DISS_degree,(DISS_institution),(DISS_advisor)*,DISS_cmte_member*,DISS_categorization)>
    -->
	<xsl:variable name="smallcase" select="'abcdefghijklmnopqrstuvwxyz'" />
	<xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'" />

	<xsl:template name="replace">
		<xsl:param name="text" />
		<xsl:param name="replace" />
		<xsl:param name="by" />
		<xsl:choose>
		  <xsl:when test="contains($text, $replace)">
		    <xsl:value-of select="substring-before($text,$replace)" />
		    <xsl:value-of select="$by" />
		    <xsl:call-template name="replace">
		      <xsl:with-param name="text"
		      select="substring-after($text,$replace)" />
		      <xsl:with-param name="replace" select="$replace" />
		      <xsl:with-param name="by" select="$by" />
		    </xsl:call-template>
		  </xsl:when>
		  <xsl:otherwise>
		    <xsl:value-of select="$text" />
		  </xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<xsl:template match="/">
		<!--<xsl:choose>
			<xsl:when test="//bulk:bulk">
				 <modsCollection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-6.xsd">
					<xsl:for-each select="//bulk:bulk/work:work">
						<mods version="3.6">
							<xsl:call-template name="work:work"/>
						</mods>
					</xsl:for-each>
				</modsCollection>
			<xsl:otherwise>-->
				<mods xmlns="http://www.loc.gov/mods/v3" xmlns:mods="http://www.loc.gov/mods/v3" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-6.xsd">
					<xsl:for-each select="//work:work">
                            <xsl:call-template name="work:work"/>
					</xsl:for-each>
				</mods>
			<!--</xsl:otherwise>
            </xsl:when>
		</xsl:choose>-->
	</xsl:template>
	<!--TITLE AND AUTHOR INFORMATION-->
	<xsl:template name="work:work">
		<xsl:for-each select="work:title">
			<titleInfo>
				<xsl:choose>
                    <xsl:when test="common:subtitle">
						<title>
							<xsl:value-of select="(translate(common:title, ':', ''))"/>
						</title>
						<subTitle>
							<xsl:value-of select="(translate(common:subtitle, ':', ''))"/>
						</subTitle>
					</xsl:when>
                        <xsl:otherwise>
							<xsl:choose>
								<xsl:when test='contains(common:title, ":")'>
									<title>
										<xsl:value-of select="substring-before(common:title, ':')"/>
									</title>
									<subTitle>
										<xsl:value-of select="substring-after(common:title, ':')"/>
									</subTitle>
								</xsl:when>
								<xsl:otherwise>
										<title>
										<xsl:value-of select="common:title"/>
										</title>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:otherwise>
				</xsl:choose>
			</titleInfo>
		</xsl:for-each>
		<name type="personal">
			<namePart type="given"></namePart>
			<namePart type="family"></namePart>
			<role>
				<roleTerm authority="marcrelator" type="text">author</roleTerm>
			</role>
			<displayForm></displayForm>
		</name>

		<!--RELATED TITLE and ABSTRACT INFORMATION: TITLEINFO and ABSTRACT-->
		<relatedItem type="host">
			<titleInfo>
				<title>
					<xsl:value-of select="work:journal-title"/>
				</title>
			</titleInfo>
			<part>
				<date><xsl:value-of select="common:publication-date/common:year"/></date>
			</part>
			<!-- Identifier for Journal -->
		<xsl:for-each select="common:external-ids/common:external-id">
			<xsl:if test="common:external-id-relationship ='part-of'">
				<identifier type="uri">
					<xsl:value-of select="common:external-id-url" />
				</identifier>
			</xsl:if>
		</xsl:for-each>
        </relatedItem>
		<!-- Identifier for Item -->
		<xsl:for-each select="common:external-ids/common:external-id">
			<xsl:if test="common:external-id-relationship ='self'">
				<identifier type="uri">
					<xsl:value-of select="common:external-id-url" />
				</identifier>
			</xsl:if>
		</xsl:for-each>
	    <xsl:for-each select="work:url">
		<location>
				<url>
					<xsl:value-of select="." />
				</url>
		</location>
         </xsl:for-each>
		<!--PUBLICATION INFORMATION: ORIGININFO -->
		<!-- Taking this part out.  <dateCreate>"create" could refer to a number of dates. Bridget used the work:accept_date as the dateIssued, so I'll stick with that for now. In dateIssued below, It's standard to use @encoding="iso8601" but the date given isn't formatted correctly.  Can this be normalized somehow?
		<xsl:for-each select="/work:submission/work:description/work:dates/work:comp_date">
					<originInfo>
						<dateCreate encoding="iso8601" keyDate="yes">
							<xsl:value-of select="/work:submission/work:description/work:dates/work:comp_date"/>
						</dateCreate>
					</originInfo>
		</xsl:for-each>-->
		<!--DATES -->
		<!--<xsl:for-each select="/work:submission/work:description/work:dates/work:comp_date">
			<originInfo>
				<dateIssued encoding="iso8601">
					<xsl:value-of select="/work:submission/work:description/work:dates/work:comp_date"/>
				</dateIssued>
                <dateCreated encoding="iso8601" keyDate="yes">
				    <xsl:value-of select="/work:submission/work:description/work:dates/work:accept_date"/>
				</dateCreated>
                <xsl:for-each select="/work:submission/work:description/work:institution/work:inst_name">
 					<publisher>
 						<xsl:value-of select="."/>
 					</publisher>
 				</xsl:for-each>
			</originInfo>
		</xsl:for-each> -->
        <!--work citation to NOTE  -->
		<xsl:for-each select="work:citation">
				<note type="citation">
					<xsl:value-of select="work:citation-value"/>
				</note>
        </xsl:for-each>
		<!-- TYPE OF RESOURCE AND EXTENT: TYPE OF RESOURCE and PHYSICAL DESCRIPTION -->
		<typeOfResource>text</typeOfResource>
		<genre><xsl:value-of select="work:type"/></genre>
	</xsl:template>
</xsl:stylesheet>
