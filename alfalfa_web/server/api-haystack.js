/***********************************************************************************************************************
 *  Copyright (c) 2008-2022, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
 *
 *  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
 *  following conditions are met:
 *
 *  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
 *  disclaimer.
 *
 *  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
 *  disclaimer in the documentation and/or other materials provided with the distribution.
 *
 *  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
 *  derived from this software without specific prior written permission from the respective party.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
 *  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 *  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
 *  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 *  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
 *  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 *  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
 *  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 ***********************************************************************************************************************/

/**
 * @openapi
 * /about:
 *   get:
 *     description: Summary information for server
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: about response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /formats:
 *   get:
 *     description: Grid data formats supported by this server
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: formats response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /hisRead:
 *   get:
 *     description: Read time series from historian
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: hisRead response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /invokeAction:
 *   get:
 *     description: Invoke action on target entity
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: invokeAction response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /nav:
 *   get:
 *     description: Navigate record tree
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: nav response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /ops:
 *   get:
 *     description: Operations supported by this server
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: ops response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /pointWrite:
 *   get:
 *     description: Read/write writable point priority array
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: pointWrite response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /read:
 *   get:
 *     description: Read entity records in database
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: read response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /watchPoll:
 *   get:
 *     description: Watch poll cov or refresh
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: watchPoll response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /watchSub:
 *   get:
 *     description: Watch subscription
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: watchSub response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */

/**
 * @openapi
 * /watchUnsub:
 *   get:
 *     description: Watch unsubscription
 *     tags:
 *       - Haystack
 *     responses:
 *       200:
 *         description: watchUnsub response
 *   servers:
 *     - url: /haystack
 *       description: Haystack server
 */
